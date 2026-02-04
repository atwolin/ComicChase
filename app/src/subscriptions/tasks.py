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
    執行每週郵件通知流程

    Args:
        sync (bool): 是否使用同步模式執行
            - True: 同步執行（適用於 Cloud Run Jobs）
            - False: 異步執行（適用於 Celery）

    Returns:
        dict: 執行結果
    """
    task_id = self.request.id if self.request.id else "sync-execution"
    logger.info(f"[{task_id}] Starting weekly notification flow (sync={sync})")

    # 偵測過去 7 天出版的新書
    last_week = timezone.now().date() - timedelta(days=7)
    new_volumes = Volume.objects.filter(
        release_date__gte=last_week,
        series__isnull=False,
    ).select_related("series")

    if not new_volumes.exists():
        logger.info(f"[{task_id}] 本週無新刊出版，將發送無新刊通知。")

    # 確保資料格式正確
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

    logger.info(f"[{task_id}] Found {len(volumes_data)} new volumes to notify")

    # 取得所有有效使用者的 ID、郵件地址與取消訂閱 token
    # 僅發送給「開啟全域郵件通知」的使用者
    User = get_user_model()
    recipients = list(
        User.objects.filter(is_active=True, receive_email=True).values_list(
            "id", "email", "unsubscribe_token"
        )
    )

    logger.info(f"[{task_id}] Found {len(recipients)} active users")

    if sync:
        # 同步模式：直接循環發送（適用於 Cloud Run Jobs）
        success_count = 0
        failed_count = 0

        for user_id, email, unsubscribe_token in recipients:
            if email:
                try:
                    # 直接調用函數（不通過 Celery），不需要傳遞 self 參數
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
                        f"({success_count}/{len(recipients)})"
                    )
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"[{task_id}] Failed to send email"
                        f" to user_id={user_id}: {str(e)}"
                    )

        result = {
            "task_id": task_id,
            "status": "completed",
            "total_recipients": len(recipients),
            "success_count": success_count,
            "failed_count": failed_count,
            "volumes_count": len(volumes_data),
        }
        logger.info(f"[{task_id}] Completed: {result}")
        return result
    else:
        # 異步模式：使用 Celery（適用於本機開發）
        for user_id, email, unsubscribe_token in recipients:
            if email:
                send_single_email_task.delay(
                    user_id,
                    email,
                    volumes_data,
                    unsubscribe_token=str(unsubscribe_token),
                )

        return {
            "task_id": task_id,
            "status": "dispatched",
            "total_recipients": len(recipients),
            "volumes_count": len(volumes_data),
        }


@shared_task(bind=True, max_retries=3)
def send_single_email_task(
    self, user_id, user_email, volumes_data, unsubscribe_token=None, sync=False
):
    """
    發送單一郵件通知

    使用 AWS SES 發送郵件，根據 AWS_USE_FEDERATION 設定決定使用：
    - Federation 模式（Cloud Run）
    - django-ses 模式（本機開發）

    Args:
        user_id (int): 使用者 ID（用於日誌記錄）
        user_email (str): 收件人郵件地址
        volumes_data (list): 新書資料列表
        unsubscribe_token (str): 用戶的取消訂閱唯一 token
        sync (bool): 是否使用同步模式執行

    Returns:
        str: 執行結果訊息
    """
    task_id = self.request.id if self and not sync else "sync-execution"

    if not volumes_data:
        subject = "【ComicChase】本週無新刊出版通知"
    else:
        subject = "【ComicChase】本週漫畫新出版清單"

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
        return f"Email sent to user_id={user_id}"
    except Exception as e:
        logger.error(f"[{task_id}] SES Send Error for user_id={user_id}: {str(e)}")
        if sync:
            # 同步模式：直接拋出異常
            raise
        else:
            # 異步模式：使用 Celery 重試機制
            raise self.retry(exc=e)
