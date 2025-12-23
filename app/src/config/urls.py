from comic.views import SeriesViewSet
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

# Router setup
router = DefaultRouter()
router.register(r"series", SeriesViewSet, basename="comics")


urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),
    # User management
    path("_allauth/", include("allauth.headless.urls")),
    # Local apps
    path("api/", include(router.urls)),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
