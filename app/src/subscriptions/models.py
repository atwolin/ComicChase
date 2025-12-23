from django.contrib.auth import get_user_model
from django.db import models


class Subscription(models.Model):
    """
    Represents a user's subscription to a comic series.
    """

    # Relationships
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    series = models.ForeignKey(
        "comic.Series",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    # Config
    receive_email = models.BooleanField(default=True)
    receive_line = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "series")
        verbose_name = "使用者追蹤漫畫列表"
        verbose_name_plural = "使用者追蹤漫畫列表"
