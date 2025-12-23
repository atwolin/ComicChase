from comic.models import Series
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from subscriptions.models import Subscription

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
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(
                user=self.user,
                series=self.series,
            )
