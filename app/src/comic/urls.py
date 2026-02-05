from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SeriesViewSet

router = DefaultRouter()
router.register(r"series", SeriesViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
