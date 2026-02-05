from django.urls import path

from .views import UnsubscribeView, UserPreferenceView

urlpatterns = [
    path("unsubscribe/", UnsubscribeView.as_view(), name="unsubscribe"),
    path("preferences/", UserPreferenceView.as_view(), name="user_preference"),
]
