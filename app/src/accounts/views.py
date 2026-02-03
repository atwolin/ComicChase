import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
def debug_env_view(request):
    """
    Temporary debug view to verify deployment and DB connection.
    """
    from django.conf import settings

    db_name = settings.DATABASES["default"]["NAME"]
    db_engine = settings.DATABASES["default"]["ENGINE"]
    db_host = settings.DATABASES["default"].get("HOST", "N/A")

    return JsonResponse(
        {
            "status": "alive",
            "version": "v2-debug",  # Bump this to verify code update
            "db_name": db_name,
            "db_engine": db_engine,
            "db_host": db_host,
            "is_sqlite": "sqlite" in db_engine,
            "secure_ssl_redirect": settings.SECURE_SSL_REDIRECT,
        }
    )


# from subscriptions.models import Subscription # Removed as we use global flag now

logger = logging.getLogger(__name__)
User = get_user_model()


@require_http_methods(["GET", "PATCH"])
@login_required
def preference_view(request):
    """
    API endpoint to get/set user preferences (receive_email).
    """
    user = request.user
    if request.method == "GET":
        # Force explicit DB fetch to ensure fresh data
        user_fresh = User.objects.get(pk=user.pk)
        response = JsonResponse(
            {
                "receive_email": user_fresh.receive_email,
                "email": user_fresh.email,
                "id": user_fresh.pk,
            }
        )
        # Prevent any caching (browser, CDN, proxy)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response

    # PATCH
    # PATCH
    try:
        data = json.loads(request.body)
        new_status = data.get("receive_email")

        # Explicitly fetch fresh user from DB to avoid any session cache issues
        user_db = User.objects.get(pk=user.pk)

        logger.info(
            f"[Preference] Before update: User {user.email} "
            f"(ID: {user.id}) receive_email={user_db.receive_email}"
        )

        if new_status is not None:
            user_db.receive_email = bool(new_status)
            user_db.save(update_fields=["receive_email"])
            logger.info(
                f"[Preference] After update: User {user.email} "
                f"updated receive_email to {user_db.receive_email}"
            )

        return JsonResponse({"receive_email": user_db.receive_email})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@require_http_methods(["GET", "POST"])
@csrf_exempt
# CSRF exempt for unsub link (or ensure CSRF handling if form post)
#  - standard Django form post has csrf token in template usually.
def unsubscribe_view(request):
    """
    處理電子郵件取消訂閱請求。

    GET 請求：顯示取消訂閱確認頁面
    POST 請求：執行取消訂閱操作

    Query Parameters:
        token: 用戶的 unsubscribe_token (UUID)
    """
    token = request.GET.get("token") or request.POST.get("token")

    logger.info(f"[Unsubscribe] Received request with token: {token}")

    if not token:
        logger.warning("[Unsubscribe] No token provided")
        return HttpResponse("無效的取消訂閱連結", status=400)

    try:
        user = User.objects.get(unsubscribe_token=token)
        logger.info(f"[Unsubscribe] Found user: {user.email} (ID: {user.id})")
    except (User.DoesNotExist, ValueError) as e:
        logger.warning(f"[Unsubscribe] Invalid token: {token}, error: {e}")
        return HttpResponse("無效的取消訂閱連結", status=400)

    if request.method == "GET":
        logger.info(f"[Unsubscribe] Showing confirmation page for {user.email}")
        return render(
            request,
            "accounts/unsubscribe_confirm.html",
            {
                "email": user.email,
                "token": token,
            },
        )

    # POST: 執行取消訂閱 - 關閉全域郵件通知
    user.receive_email = False
    user.save()

    logger.info(f"[Unsubscribe] Disabled global email for {user.email}")

    return render(
        request,
        "accounts/unsubscribe_success.html",
        {
            "email": user.email,
        },
    )
