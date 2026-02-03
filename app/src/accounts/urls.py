from django.urls import path

from .views import debug_env_view, preference_view, unsubscribe_view

urlpatterns = [
    path("unsubscribe/", unsubscribe_view, name="unsubscribe"),
    path("preferences/", preference_view, name="user_preference"),
    path("debug-env/", debug_env_view, name="debug_env"),
]
