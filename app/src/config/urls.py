from comic.views import SeriesViewSet
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

# 建立 DRF router
router = DefaultRouter()
router.register(r"series", SeriesViewSet, basename="comics")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
