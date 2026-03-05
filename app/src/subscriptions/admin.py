from django.contrib import admin

from .models import NotificationLog, Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "series", "receive_email", "receive_line"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "series__title"]


class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["volume", "sent_at"]
    list_filter = ["sent_at"]
    search_fields = ["volume__series__title_tw"]
    readonly_fields = ["volume", "sent_at"]


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(NotificationLog, NotificationLogAdmin)
