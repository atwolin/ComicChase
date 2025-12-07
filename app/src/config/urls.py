from comic.views import (
    CurrentUserView,
    RegisterView,
    SeriesViewSet,
    UserCollectionViewSet,
)
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# 建立 DRF router
router = DefaultRouter()
router.register(r"series", SeriesViewSet, basename="comics")
router.register(r"collections", UserCollectionViewSet, basename="collections")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    # 認證相關
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", CurrentUserView.as_view(), name="current_user"),
]
