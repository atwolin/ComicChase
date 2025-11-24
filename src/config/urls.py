from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from comic.views import SeriesViewSet

# 建立 DRF router
router = DefaultRouter()
router.register(r'series', SeriesViewSet, basename='series') 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), 
]
