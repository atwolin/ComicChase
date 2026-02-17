from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.constraints import UniqueConstraint


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
        constraints = [
            UniqueConstraint(fields=["user", "series"], name="unique_subscription")
        ]
        ordering = ["-created_at"]
        verbose_name = "使用者追蹤漫畫列表"
        verbose_name_plural = "使用者追蹤漫畫列表"

    def __str__(self):
        return f"{self.user.username} → {self.series}"


class NotificationLog(models.Model):
    """
    記錄每位使用者已被通知過的單行本。
    用於防止重複寄信，並確保延遲入庫的書籍不會被遺漏。
    """

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    volume = models.ForeignKey(
        "comic.Volume",
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "volume"],
                name="unique_notification_per_user_volume",
            )
        ]
        ordering = ["-sent_at"]
        verbose_name = "通知紀錄"
        verbose_name_plural = "通知紀錄"

    def __str__(self):
        return f"{self.user.username} ← {self.volume} @ {self.sent_at}"
