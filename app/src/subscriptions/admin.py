from django.contrib import admin

from .models import Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "series", "receive_email", "receive_line"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "series__title"]


admin.site.register(Subscription, SubscriptionAdmin)
