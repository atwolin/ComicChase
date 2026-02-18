import logging
from collections import defaultdict

from celery import chain, shared_task
from comic.models import Volume
from comic_scrapers.tasks import crawl_new_volumes_bookstw, crawl_orphan_volumes_eslite
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from subscriptions.models import Subscription

logger = logging.getLogger(__name__)


@shared_task
def master_weekly_update_job():
    """
    串聯爬蟲與通知流程
    """
    job = chain(
        crawl_new_volumes_bookstw.si(),
        crawl_orphan_volumes_eslite.si(),
        run_weekly_notification_flow.si(),
    )
    job.apply_async()
    return "Master workflow triggered."


@shared_task(bind=True)
def run_weekly_notification_flow(self, sync=False):
    """
    執行郵件通知流程

    為每位使用者篩選其訂閱中「尚未通知過」的新書，避免重複寄信。
    篩選條件：volume.created_at > subscription.last_notified_at（或 created_at）

    Args:
        sync (bool): 是否使用同步模式執行
            - True: 同步執行（適用於 Cloud Run Jobs）
            - False: 異步執行（適用於 Celery）

    Returns:
        dict: 執行結果
    """
    task_id = self.request.id if self.request.id else "sync-execution"
    logger.info(f"[{task_id}] Starting notification flow (sync={sync})")

    # 取得所有有效使用者（全域 receive_email=True）
    User = get_user_model()
    recipients = list(
        User.objects.filter(
            is_active=True,
            receive_email=True,
            unsubscribe_token__isnull=False,
        ).values_list("id", "email", "unsubscribe_token")
    )

    logger.info(f"[{task_id}] Found {len(recipients)} active users")

    if not recipients:
        logger.info(f"[{task_id}] No active recipients, skipping.")
        return {"task_id": task_id, "status": "skipped", "reason": "no_recipients"}

    recipient_ids = [r[0] for r in recipients]

    # 一次查詢所有收件人的訂閱（僅 receive_email=True）
    # 取得 (subscription_id, user_id, series_id, last_notified_at, created_at)
    subscriptions = list(
        Subscription.objects.filter(
            user_id__in=recipient_ids,
            receive_email=True,
        ).values_list("id", "user_id", "series_id", "last_notified_at", "created_at")
    )

    # 建立 per-user 訂閱資訊：user_id → [(sub_id, series_id, cutoff_time), ...]
    # cutoff_time = last_notified_at ?? created_at（從訂閱時間開始算）
    user_subs_map = defaultdict(list)
    for sub_id, user_id, series_id, last_notified_at, created_at in subscriptions:
        cutoff = last_notified_at or created_at
        user_subs_map[user_id].append((sub_id, series_id, cutoff))

    # 取得候選 volumes（以最早的 cutoff 為下界）
    all_cutoffs = [cutoff for subs in user_subs_map.values() for _, _, cutoff in subs]
    if not all_cutoffs:
        logger.info(f"[{task_id}] No active subscriptions, skipping.")
        return {"task_id": task_id, "status": "skipped", "reason": "no_subscriptions"}

    earliest_cutoff = min(all_cutoffs)
    all_volumes = list(
        Volume.objects.filter(
            series__isnull=False,
            release_date__isnull=False,
            created_at__gt=earliest_cutoff,
        ).select_related("series")
    )

    logger.info(f"[{task_id}] Candidate volumes: {len(all_volumes)}")

    # 依 series_id 分組 volumes，加速查詢
    volumes_by_series = defaultdict(list)
    for v in all_volumes:
        volumes_by_series[v.series_id].append(v)

    if sync:
        # 同步模式：直接循環發送（適用於 Cloud Run Jobs）
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for user_id, email, unsubscribe_token in recipients:
            if not email:
                continue

            user_subs = user_subs_map.get(user_id, [])
            if not user_subs:
                skipped_count += 1
                continue

            user_volumes, sub_ids = _get_unsent_volumes_for_user(
                volumes_by_series, user_subs
            )

            if not user_volumes:
                skipped_count += 1
                logger.info(
                    f"[{task_id}] No new volumes for user_id={user_id}, skipping."
                )
                continue

            try:
                send_single_email_task(
                    user_id,
                    email,
                    user_volumes,
                    subscription_ids=sub_ids,
                    unsubscribe_token=str(unsubscribe_token),
                    sync=True,
                )
                success_count += 1
                logger.info(
                    f"[{task_id}] Email sent to user_id={user_id} "
                    f"with {len(user_volumes)} volumes "
                    f"({success_count}/{len(recipients)})"
                )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"[{task_id}] Failed to send email to user_id={user_id}: {str(e)}"
                )

        result = {
            "task_id": task_id,
            "status": "completed",
            "total_recipients": len(recipients),
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
        }
        logger.info(f"[{task_id}] Completed: {result}")
        return result
    else:
        # 異步模式：使用 Celery（適用於本機開發）
        dispatched_count = 0
        for user_id, email, unsubscribe_token in recipients:
            if not email:
                continue

            user_subs = user_subs_map.get(user_id, [])
            if not user_subs:
                continue

            user_volumes, sub_ids = _get_unsent_volumes_for_user(
                volumes_by_series, user_subs
            )

            if not user_volumes:
                continue

            send_single_email_task.delay(
                user_id,
                email,
                user_volumes,
                subscription_ids=sub_ids,
                unsubscribe_token=str(unsubscribe_token),
            )
            dispatched_count += 1

        return {
            "task_id": task_id,
            "status": "dispatched",
            "total_recipients": len(recipients),
            "dispatched_count": dispatched_count,
        }


def _get_unsent_volumes_for_user(volumes_by_series, user_subs):
    """
    為指定使用者篩選尚未通知的新書。

    Args:
        volumes_by_series: dict[series_id, list[Volume]]，依系列分組的候選 volumes
        user_subs: list[(sub_id, series_id, cutoff_time)]，使用者的訂閱清單

    Returns:
        tuple: (volumes_data list, subscription_ids list)
    """
    user_new_volumes = []
    triggered_sub_ids = set()

    for sub_id, series_id, cutoff in user_subs:
        series_volumes = volumes_by_series.get(series_id, [])
        for v in series_volumes:
            if v.created_at > cutoff:
                user_new_volumes.append(v)
                triggered_sub_ids.add(sub_id)

    volumes_data = [
        {
            "title": v.series.title_tw or v.series.title_jp,
            "volume_number": v.volume_number,
            "region": v.get_region_display(),
            "release_date": v.release_date.strftime("%Y-%m-%d"),
            "image_url": v.image_url,
        }
        for v in user_new_volumes
    ]

    return volumes_data, list(triggered_sub_ids)


@shared_task(bind=True, max_retries=3)
def send_single_email_task(
    self,
    user_id,
    user_email,
    volumes_data,
    subscription_ids=None,
    unsubscribe_token=None,
    sync=False,
):
    """
    發送單一郵件通知，並在成功後更新 Subscription.last_notified_at。

    使用 AWS SES 發送郵件，根據 AWS_USE_FEDERATION 設定決定使用：
    - Federation 模式（Cloud Run）
    - django-ses 模式（本機開發）

    Args:
        user_id (int): 使用者 ID（用於日誌記錄）
        user_email (str): 收件人郵件地址
        volumes_data (list): 新書資料列表
        subscription_ids (list[int]): 需要更新 last_notified_at 的 Subscription PK 列表
        unsubscribe_token (str): 用戶的取消訂閱唯一 token
        sync (bool): 是否使用同步模式執行

    Returns:
        str: 執行結果訊息
    """
    task_id = self.request.id if self and not sync else "sync-execution"

    subject = "【ComicChase】漫畫新出版通知"

    # 檢查渲染前的內容
    logger.info(
        f"[{task_id}] Rendering template for user_id={user_id} "
        f"with {len(volumes_data)} items"
    )
    if volumes_data:
        logger.info(f"[{task_id}] Sample image URL: {volumes_data[0]['image_url']}")

    # 渲染 HTML 內容
    html_content = render_to_string(
        "emails/weekly_digest.html",
        {
            "volumes": volumes_data,
            "site_url": settings.FRONTEND_URL,
            "unsubscribe_token": unsubscribe_token,
        },
    )

    # 檢查渲染後的內容
    if "{%" in html_content or "{{" in html_content:
        logger.error(f"[{task_id}] Template rendering failed! Tags are still present.")

    # 執行發送
    try:
        use_federation = getattr(settings, "AWS_USE_FEDERATION", False)

        if use_federation:
            # Use Google-to-AWS Federation
            logger.info(f"[{task_id}] Sending email via Federation to {user_email}")
            from config.aws_federation import send_email_with_federation

            send_email_with_federation(
                source=settings.DEFAULT_FROM_EMAIL,
                to_addresses=[user_email],
                subject=subject,
                body_text="請在支援 HTML 的環境查看此郵件",
                body_html=html_content,
            )
        else:
            # Use django-ses with static credentials
            logger.info(f"[{task_id}] Sending email via django-ses to {user_email}")
            msg = EmailMultiAlternatives(
                subject=subject,
                body="請在支援 HTML 的環境查看此郵件",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        logger.info(f"[{task_id}] Email sent successfully to user_id={user_id}")
    except Exception as e:
        logger.error(f"[{task_id}] SES Send Error for user_id={user_id}: {str(e)}")
        if sync:
            # 同步模式：直接拋出異常
            raise
        else:
            # 異步模式：使用 Celery 重試機制
            raise self.retry(exc=e)

    # 寄信成功後，更新 Subscription.last_notified_at
    # 獨立 try/except：DB 更新失敗不應觸發重寄信件
    if subscription_ids:
        try:
            now = timezone.now()
            updated = Subscription.objects.filter(
                id__in=subscription_ids,
            ).update(last_notified_at=now)
            logger.info(
                f"[{task_id}] Updated last_notified_at for {updated} subscriptions "
                f"of user_id={user_id}"
            )
        except Exception as e:
            logger.error(
                f"[{task_id}] Failed to update last_notified_at "
                f"for user_id={user_id}: {str(e)}"
            )

    return f"Email sent to user_id={user_id}"
