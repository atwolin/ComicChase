from django.contrib import admin

from .models import Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "series",
        "receive_email",
        "receive_line",
        "last_notified_at",
    ]
    list_filter = ["created_at", "last_notified_at"]
    search_fields = ["user__username", "series__title_tw"]


admin.site.register(Subscription, SubscriptionAdmin)
