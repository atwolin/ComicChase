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

    # 通知追蹤：記錄此訂閱最後一次成功發送通知的時間
    # 新建訂閱時為 null，首次通知流程會將其設為 created_at
    # 之後每次成功寄信後更新為 now()
    last_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="此訂閱最後一次成功發送通知的時間",
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "series"], name="unique_subscription")
        ]
        ordering = ["-created_at"]
        verbose_name = "使用者追蹤漫畫列表"
        verbose_name_plural = "使用者追蹤漫畫列表"

    def __str__(self):
        return f"{self.user.username} → {self.series}"
