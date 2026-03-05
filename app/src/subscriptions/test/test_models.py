from comic.models import Series, Volume
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from subscriptions.models import NotificationLog, Subscription

User = get_user_model()


class SubscriptionModelTest(TestCase):
    def setUp(self):
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


class NotificationLogModelTest(TestCase):
    def setUp(self):
        self.series = Series.objects.create(
            title_tw="測試系列",
            title_jp="テストシリーズ",
            author_tw="測試作者",
            author_jp="テスト著者",
        )
        self.volume = Volume.objects.create(
            series=self.series,
            region="TW",
            volume_number=1,
            release_date="2026-02-01",
        )

    def test_create_notification_log(self):
        """驗證可正常建立通知紀錄。"""
        log = NotificationLog.objects.create(
            volume=self.volume,
        )
        self.assertEqual(log.volume, self.volume)
        self.assertIsNotNone(log.sent_at)

    def test_prevent_duplicate_notification_log(self):
        """驗證 UniqueConstraint 阻止同一 volume 重複紀錄。"""
        NotificationLog.objects.create(
            volume=self.volume,
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                NotificationLog.objects.create(
                    volume=self.volume,
                )

    def test_notification_log_str(self):
        """驗證 __str__ 輸出包含書籍資訊。"""
        log = NotificationLog.objects.create(
            volume=self.volume,
        )
        result = str(log)
        self.assertIn("測試系列", result)
