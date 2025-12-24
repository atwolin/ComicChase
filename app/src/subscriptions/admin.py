from django.contrib import admin

from .models import Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "series", "receive_email", "receive_line")


admin.site.register(Subscription, SubscriptionAdmin)
