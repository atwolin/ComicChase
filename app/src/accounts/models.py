import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Attributes:
        unsubscribe_token: Unique token for email unsubscribe functionality.
            This token is auto-generated and used to verify unsubscribe requests
            without requiring user authentication.
    """

    unsubscribe_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="用於電子郵件取消訂閱的唯一識別碼",
    )

    receive_email = models.BooleanField(
        default=True,
        help_text="接收每週新書通知",
        verbose_name="接收郵件通知",
    )
