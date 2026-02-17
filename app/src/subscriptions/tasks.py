import logging

from celery import chain, shared_task
from comic.models import Volume
from comic_scrapers.tasks import crawl_new_volumes_bookstw, crawl_orphan_volumes_eslite
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from subscriptions.models import NotificationLog

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

    為每位使用者篩選「尚未通知過」的新書，避免重複寄信與漏信。
    篩選條件：
      1. volume.created_at > user.date_joined（排除使用者加入前就存在的舊書）
      2. 排除已在 NotificationLog 中的 volume（防止重複通知）

    Args:
        sync (bool): 是否使用同步模式執行
            - True: 同步執行（適用於 Cloud Run Jobs）
            - False: 異步執行（適用於 Celery）

    Returns:
        dict: 執行結果
    """
    task_id = self.request.id if self.request.id else "sync-execution"
    logger.info(f"[{task_id}] Starting notification flow (sync={sync})")

    # 取得所有已入庫且有系列的 volumes（不再限制 7 天窗口）
    all_volumes = list(
        Volume.objects.filter(
            series__isnull=False,
            release_date__isnull=False,
        ).select_related("series")
    )

    logger.info(f"[{task_id}] Total volumes in DB: {len(all_volumes)}")

    # 取得所有有效使用者
    # 僅發送給「開啟全域郵件通知」的使用者
    User = get_user_model()
    recipients = list(
        User.objects.filter(
            is_active=True,
            receive_email=True,
            unsubscribe_token__isnull=False,
        ).values_list("id", "email", "unsubscribe_token", "date_joined")
    )

    logger.info(f"[{task_id}] Found {len(recipients)} active users")

    if sync:
        # 同步模式：直接循環發送（適用於 Cloud Run Jobs）
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for user_id, email, unsubscribe_token, date_joined in recipients:
            if not email:
                continue

            # 篩選此使用者尚未通知的新書
            user_volumes, user_volume_ids = _get_unsent_volumes_for_user(
                all_volumes, user_id, date_joined
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
                    volume_ids=user_volume_ids,
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
        for user_id, email, unsubscribe_token, date_joined in recipients:
            if not email:
                continue

            user_volumes, user_volume_ids = _get_unsent_volumes_for_user(
                all_volumes, user_id, date_joined
            )

            if not user_volumes:
                continue

            send_single_email_task.delay(
                user_id,
                email,
                user_volumes,
                volume_ids=user_volume_ids,
                unsubscribe_token=str(unsubscribe_token),
            )
            dispatched_count += 1

        return {
            "task_id": task_id,
            "status": "dispatched",
            "total_recipients": len(recipients),
            "dispatched_count": dispatched_count,
        }


def _get_unsent_volumes_for_user(all_volumes, user_id, date_joined):
    """
    為指定使用者篩選尚未通知的新書。

    Args:
        all_volumes: 所有 Volume queryset（已 select_related）
        user_id: 使用者 ID
        date_joined: 使用者加入時間（datetime）

    Returns:
        tuple: (volumes_data list, volume_ids list)
    """
    # 取得此使用者已通知過的 volume IDs
    notified_volume_ids = set(
        NotificationLog.objects.filter(user_id=user_id).values_list(
            "volume_id", flat=True
        )
    )

    # 篩選條件：
    # 1. volume.created_at > user.date_joined（排除舊書）
    # 2. 尚未在 NotificationLog 中（防重複）
    user_new_volumes = [
        v
        for v in all_volumes
        if v.created_at > date_joined and v.id not in notified_volume_ids
    ]

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
    volume_ids = [v.id for v in user_new_volumes]

    return volumes_data, volume_ids


@shared_task(bind=True, max_retries=3)
def send_single_email_task(
    self,
    user_id,
    user_email,
    volumes_data,
    volume_ids=None,
    unsubscribe_token=None,
    sync=False,
):
    """
    發送單一郵件通知，並在成功後寫入 NotificationLog。

    使用 AWS SES 發送郵件，根據 AWS_USE_FEDERATION 設定決定使用：
    - Federation 模式（Cloud Run）
    - django-ses 模式（本機開發）

    Args:
        user_id (int): 使用者 ID（用於日誌記錄）
        user_email (str): 收件人郵件地址
        volumes_data (list): 新書資料列表
        volume_ids (list[int]): 對應的 Volume PK 列表，用於寫入 NotificationLog
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

        # 寄信成功後，寫入 NotificationLog 防止重複通知
        if volume_ids:
            NotificationLog.objects.bulk_create(
                [NotificationLog(user_id=user_id, volume_id=vid) for vid in volume_ids],
                ignore_conflicts=True,  # 防止 race condition 導致的重複
            )
            logger.info(
                f"[{task_id}] Logged {len(volume_ids)} notification records "
                f"for user_id={user_id}"
            )

        logger.info(f"[{task_id}] Email sent successfully to user_id={user_id}")
        return f"Email sent to user_id={user_id}"
    except Exception as e:
        logger.error(f"[{task_id}] SES Send Error for user_id={user_id}: {str(e)}")
        if sync:
            # 同步模式：直接拋出異常
            raise
        else:
            # 異步模式：使用 Celery 重試機制
            raise self.retry(exc=e)
