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

    # 取得所有有效使用者的 ID 與郵件地址
    User = get_user_model()
    recipients = list(User.objects.filter(is_active=True).values_list("id", "email"))

    logger.info(f"[{task_id}] Found {len(recipients)} active users")

    if sync:
        # 同步模式：直接循環發送（適用於 Cloud Run Jobs）
        success_count = 0
        failed_count = 0

        for user_id, email in recipients:
            if email:
                try:
                    # 直接調用函數（不通過 Celery），不需要傳遞 self 參數
                    send_single_email_task(user_id, email, volumes_data, sync=True)
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
        for user_id, email in recipients:
            if email:
                send_single_email_task.delay(user_id, email, volumes_data)

        return {
            "task_id": task_id,
            "status": "dispatched",
            "total_recipients": len(recipients),
            "volumes_count": len(volumes_data),
        }


@shared_task(bind=True, max_retries=3)
def send_single_email_task(self, user_id, user_email, volumes_data, sync=False):
    """
    發送單一郵件通知

    使用 AWS SES 發送郵件，根據 AWS_USE_FEDERATION 設定決定使用：
    - Federation 模式（Cloud Run）
    - django-ses 模式（本機開發）

    Args:
        user_id (int): 使用者 ID（用於日誌記錄）
        user_email (str): 收件人郵件地址
        volumes_data (list): 新書資料列表
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
        {"volumes": volumes_data, "site_url": "https://comicchase.site"},
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


@shared_task(bind=True)
def run_daily_subscription_notification(self, sync=False):
    """
    執行每日訂閱通知流程

    對於每位有訂閱的使用者，檢查其訂閱的系列是否有新卷，
    若有則發送個人化通知郵件。

    Args:
        sync (bool): 是否使用同步模式執行
            - True: 同步執行（適用於 Cloud Run Jobs）
            - False: 異步執行（適用於 Celery）

    Returns:
        dict: 執行結果
    """
    from subscriptions.models import Subscription

    task_id = self.request.id if self.request.id else "sync-execution"
    logger.info(f"[{task_id}] Starting daily subscription notification (sync={sync})")

    # 取得所有啟用郵件通知的訂閱
    subscriptions = Subscription.objects.filter(
        receive_email=True,
        user__is_active=True,
    ).select_related("user", "series")

    # 按使用者分組
    user_subscriptions = {}
    for sub in subscriptions:
        if sub.user.email:
            if sub.user_id not in user_subscriptions:
                user_subscriptions[sub.user_id] = {
                    "email": sub.user.email,
                    "subscriptions": [],
                }
            user_subscriptions[sub.user_id]["subscriptions"].append(sub)

    logger.info(f"[{task_id}] Found {len(user_subscriptions)} users with subscriptions")

    success_count = 0
    failed_count = 0
    emails_sent = 0

    for user_id, user_data in user_subscriptions.items():
        try:
            # 取得該使用者需要通知的新卷
            new_volumes = []
            subscriptions_to_update = []

            for sub in user_data["subscriptions"]:
                # 查詢該系列在 last_notified_at 之後新增的卷
                volumes_query = Volume.objects.filter(
                    series=sub.series,
                    series__isnull=False,
                )

                if sub.last_notified_at:
                    # 使用 release_date 或 created_at 判斷新卷
                    # 考慮爬蟲可能補抓舊資料，所以用 created_at
                    volumes_query = volumes_query.filter(
                        release_date__gt=sub.last_notified_at.date()
                    )
                else:
                    # 首次通知：只通知過去 7 天內的新卷
                    last_week = timezone.now().date() - timedelta(days=7)
                    volumes_query = volumes_query.filter(release_date__gte=last_week)

                series_new_volumes = list(volumes_query.select_related("series"))
                if series_new_volumes:
                    new_volumes.extend(series_new_volumes)
                    subscriptions_to_update.append(sub)

            if not new_volumes:
                success_count += 1
                continue

            # 準備郵件內容
            volumes_data = [
                {
                    "title": v.series.title_tw or v.series.title_jp,
                    "volume_number": v.volume_number,
                    "region": v.get_region_display(),
                    "release_date": v.release_date.strftime("%Y-%m-%d")
                    if v.release_date
                    else "未知",
                    "image_url": v.image_url,
                }
                for v in new_volumes
            ]

            # 取得要更新的訂閱 ID
            subscription_ids = [sub.id for sub in subscriptions_to_update]

            # 發送郵件
            if sync:
                # 同步模式：發送後直接更新 last_notified_at
                send_subscription_email(
                    user_id, user_data["email"], volumes_data, sync=True
                )
                # 同步成功後更新 last_notified_at
                now = timezone.now()
                for sub in subscriptions_to_update:
                    sub.last_notified_at = now
                Subscription.objects.bulk_update(
                    subscriptions_to_update, ["last_notified_at"]
                )
            else:
                # 非同步模式：將訂閱 ID 傳給 async task
                # last_notified_at 將在郵件成功發送後由 async task 更新
                send_subscription_email.delay(
                    user_id,
                    user_data["email"],
                    volumes_data,
                    subscription_ids=subscription_ids,
                )

            success_count += 1
            emails_sent += 1
            logger.info(
                f"[{task_id}] Notification {'sent' if sync else 'enqueued'} "
                f"for user_id={user_id} with {len(new_volumes)} new volumes"
            )

        except Exception as e:
            failed_count += 1
            logger.error(f"[{task_id}] Failed to process user_id={user_id}: {str(e)}")
            if not sync:
                continue
            raise

    result = {
        "task_id": task_id,
        "status": "completed",
        "total_users": len(user_subscriptions),
        "success_count": success_count,
        "failed_count": failed_count,
        "emails_sent": emails_sent,
    }
    logger.info(f"[{task_id}] Completed: {result}")
    return result


@shared_task(bind=True, max_retries=3)
def send_subscription_email(
    self, user_id, user_email, volumes_data, sync=False, subscription_ids=None
):
    """
    發送訂閱新書通知郵件

    Args:
        user_id (int): 使用者 ID
        user_email (str): 收件人郵件地址
        volumes_data (list): 新書資料列表
        sync (bool): 是否使用同步模式執行
        subscription_ids (list[int], optional): 要更新 last_notified_at 的訂閱 ID 列表
            （僅用於非同步模式，成功發送後更新）

    Returns:
        str: 執行結果訊息
    """
    task_id = self.request.id if self and not sync else "sync-execution"

    subject = f"【ComicChase】您追蹤的漫畫有 {len(volumes_data)} 本新書上架！"

    logger.info(
        f"[{task_id}] Rendering subscription notification for user_id={user_id} "
        f"with {len(volumes_data)} items"
    )

    # 渲染 HTML 內容
    html_content = render_to_string(
        "emails/subscription_notification.html",
        {"volumes": volumes_data, "site_url": "https://comicchase.site"},
    )

    try:
        use_federation = getattr(settings, "AWS_USE_FEDERATION", False)

        if use_federation:
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
            logger.info(f"[{task_id}] Sending email via django-ses to {user_email}")
            msg = EmailMultiAlternatives(
                subject=subject,
                body="請在支援 HTML 的環境查看此郵件",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        # 成功發送後更新 last_notified_at（僅非同步模式）
        if subscription_ids and not sync:
            updated_count = Subscription.objects.filter(id__in=subscription_ids).update(
                last_notified_at=timezone.now()
            )
            logger.info(
                f"[{task_id}] Updated last_notified_at "
                f"for {updated_count} subscriptions"
            )

        logger.info(f"[{task_id}] Subscription email sent to user_id={user_id}")
        return f"Subscription email sent to user_id={user_id}"
    except Exception as e:
        logger.error(f"[{task_id}] SES Send Error for user_id={user_id}: {str(e)}")
        if sync:
            raise
        else:
            raise self.retry(exc=e)
