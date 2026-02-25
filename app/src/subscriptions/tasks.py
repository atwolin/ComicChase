import logging
from datetime import timedelta

from celery import chain, shared_task
from comic.models import Volume
from comic_scrapers.tasks import crawl_new_volumes_bookstw, crawl_orphan_volumes_eslite
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

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
        cleanup_old_notification_logs.si(),
    )
    job.apply_async()
    return "Master workflow triggered."


@shared_task
def cleanup_old_notification_logs():
    """
    清理超過 30 天的 NotificationLog 紀錄。
    因為新書查詢只看過去 10 天，舊紀錄不會再被查到，定期清理避免 DB 膨脹。
    """
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = NotificationLog.objects.filter(sent_at__lt=cutoff).delete()
    logger.info(f"Deleted {deleted} old NotificationLog entries")
    return {"deleted_count": deleted}


@shared_task(bind=True)
def run_weekly_notification_flow(self, sync=False):
    """
    執行郵件通知流程

    全域查出尚未通知的新書，對所有使用者發送相同內容的通知信。
    資料延遲對所有使用者一致，因此新書判斷只需全域做一次。

    Args:
        sync (bool): 是否使用同步模式執行
            - True: 同步執行（適用於 Cloud Run Jobs）
            - False: 異步執行（適用於 Celery）

    Returns:
        dict: 執行結果
    """
    task_id = self.request.id if self.request.id else "sync-execution"
    logger.info(f"[{task_id}] Starting notification flow (sync={sync})")

    # ── 1. 全域查出尚未通知的 volumes ──
    # 限制 release_date 在過去 10 天內（7 天 + 3 天 buffer），避免首次部署或
    # NotificationLog 被清空時寄出全部歷史書籍
    cutoff_date = timezone.now().date() - timedelta(days=10)
    notified_volume_qs = NotificationLog.objects.values_list("volume_id", flat=True)
    new_volumes = list(
        Volume.objects.filter(
            series__isnull=False,
            release_date__gte=cutoff_date,
        )
        .exclude(id__in=notified_volume_qs)
        .select_related("series")
    )

    logger.info(f"[{task_id}] New volumes to notify: {len(new_volumes)}")

    if not new_volumes:
        result = {
            "task_id": task_id,
            "status": "no_new_volumes",
            "message": "No new volumes to notify.",
        }
        logger.info(f"[{task_id}] {result}")
        return result

    # ── 2. 準備通知資料（所有使用者共用） ──
    volumes_data = [
        {
            "title": v.series.title_tw or v.series.title_jp,
            "volume_number": v.volume_number,
            "region": v.get_region_display(),
            "release_date": v.release_date.strftime("%Y-%m-%d"),
            "image_url": v.image_url,
        }
        for v in new_volumes
    ]
    new_volume_ids = [v.id for v in new_volumes]

    # ── 3. 取得所有有效收件人 ──
    User = get_user_model()
    recipients = list(
        User.objects.filter(
            is_active=True,
            receive_email=True,
            unsubscribe_token__isnull=False,
        ).values_list("id", "email", "unsubscribe_token")
    )

    logger.info(f"[{task_id}] Found {len(recipients)} active recipients")

    # ── 4. 寄送郵件 ──
    if sync:
        # 同步模式：直接循環發送（適用於 Cloud Run Jobs）
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for user_id, email, unsubscribe_token in recipients:
            if not email:
                skipped_count += 1
                continue

            try:
                send_single_email_task(
                    user_id,
                    email,
                    volumes_data,
                    unsubscribe_token=str(unsubscribe_token),
                    sync=True,
                )
                success_count += 1
                logger.info(
                    f"[{task_id}] Email sent to user_id={user_id} "
                    f"with {len(volumes_data)} volumes "
                    f"({success_count}/{len(recipients)})"
                )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"[{task_id}] Failed to send email to user_id={user_id}: {str(e)}"
                )

        # ── 5a. 同步模式：全域寫入 NotificationLog ──
        # 僅在至少有一封信成功寄出時才標記，避免全部失敗卻標記為已通知
        if success_count > 0:
            NotificationLog.objects.bulk_create(
                [NotificationLog(volume_id=vid) for vid in new_volume_ids],
                ignore_conflicts=True,
            )
            logger.info(
                f"[{task_id}] Logged {len(new_volume_ids)} volumes to NotificationLog"
            )
        else:
            logger.warning(
                f"[{task_id}] All sends failed, skipping NotificationLog write"
            )
    else:
        # 異步模式：使用 Celery（適用於本機開發）
        # 注意：異步模式下 NotificationLog 由 send_single_email_task 在寄信成功後寫入，
        # 避免在尚未確認送達前就標記為已通知
        skipped_count = 0
        success_count = 0
        failed_count = 0

        for user_id, email, unsubscribe_token in recipients:
            if not email:
                skipped_count += 1
                continue

            try:
                send_single_email_task.delay(
                    user_id,
                    email,
                    volumes_data,
                    volume_ids=new_volume_ids,
                    unsubscribe_token=str(unsubscribe_token),
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"[{task_id}] Failed to dispatch email task "
                    f"for user_id={user_id}: {str(e)}"
                )

    result = {
        "task_id": task_id,
        "status": "completed" if sync else "dispatched",
        "total_recipients": len(recipients),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "new_volumes_count": len(new_volume_ids),
    }
    logger.info(f"[{task_id}] Completed: {result}")
    return result


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
    發送單一郵件通知。

    使用 AWS SES 發送郵件，根據 AWS_USE_FEDERATION 設定決定使用：
    - Federation 模式（Cloud Run）
    - django-ses 模式（本機開發）

    同步模式下，NotificationLog 由上層 run_weekly_notification_flow 統一寫入。
    異步模式下，本 task 在寄信成功後自行寫入 NotificationLog，
    確保只有成功送達的信件才會被標記為已通知。

    Args:
        user_id (int): 使用者 ID（用於日誌記錄）
        user_email (str): 收件人郵件地址
        volumes_data (list): 新書資料列表
        volume_ids (list[int]): 對應的 Volume PK 列表（異步模式用於寫入 NotificationLog)
        unsubscribe_token (str): 用戶的取消訂閱唯一 token
        sync (bool): 是否使用同步模式執行

    Returns:
        str: 執行結果訊息
    """
    task_id = self.request.id if not sync else "sync-execution"

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

        # 異步模式：寄信成功後寫入 NotificationLog
        if volume_ids and not sync:
            NotificationLog.objects.bulk_create(
                [NotificationLog(volume_id=vid) for vid in volume_ids],
                ignore_conflicts=True,
            )
            logger.info(
                f"[{task_id}] Logged {len(volume_ids)} volumes to NotificationLog"
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
