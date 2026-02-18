from comic.models import Series
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from subscriptions.models import Subscription

User = get_user_model()


class BaseSubscriptionMixin:
    """共用的測試 mixin，建立 user 和 series。"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@email.com",
            password="testpassword123",
        )
        self.series = Series.objects.create(
            title_tw="測試系列",
            title_jp="テストシリーズ",
            author_tw="測試作者",
            author_jp="テスト著者",
        )


class SubscriptionModelTest(BaseSubscriptionMixin, TestCase):
    def test_create_subscription(self):
        subscription = Subscription.objects.create(
            user=self.user,
            series=self.series,
            receive_email=False,
            receive_line=True,
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.series, self.series)
        self.assertFalse(subscription.receive_email)
        self.assertTrue(subscription.receive_line)

    def test_prevent_duplicate_subscription(self):
        Subscription.objects.create(
            user=self.user,
            series=self.series,
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Subscription.objects.create(
                    user=self.user,
                    series=self.series,
                )

    def test_last_notified_at_defaults_to_none(self):
        """新建訂閱時 last_notified_at 預設為 None。"""
        subscription = Subscription.objects.create(
            user=self.user,
            series=self.series,
        )
        self.assertIsNone(subscription.last_notified_at)

    def test_last_notified_at_can_be_updated(self):
        """驗證 last_notified_at 可以成功更新。"""
        subscription = Subscription.objects.create(
            user=self.user,
            series=self.series,
        )
        now = timezone.now()
        Subscription.objects.filter(id=subscription.id).update(last_notified_at=now)
        subscription.refresh_from_db()
        self.assertEqual(subscription.last_notified_at, now)

    def test_subscription_str(self):
        """驗證 Subscription.__str__ 回傳格式。
        注意：此測試隱含依賴 Series.__str__（預期回傳 title_tw）。
        """
        subscription = Subscription.objects.create(
            user=self.user,
            series=self.series,
        )
        result = str(subscription)
        self.assertIn("testuser", result)
        self.assertIn("測試系列", result)
