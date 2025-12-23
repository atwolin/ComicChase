"""
Tests for Subscription API endpoints.

TESTING PHILOSOPHY:
We only test our CUSTOM business logic, not Django/DRF built-in features.

What we TEST:
✅ Custom ViewSet actions (destroy_by_series)
✅ Custom queryset filtering (user isolation via get_queryset)
✅ Custom permission combinations (IsAuthenticated + IsOwner + queryset)
✅ Custom serializer behavior (HiddenField with CurrentUserDefault)

What we DON'T test (already tested by Django/DRF):
❌ Basic CRUD operations (ModelViewSet provides these)
❌ Built-in validators (UniqueTogetherValidator)
❌ HTTP status codes for standard operations
❌ Permission classes behavior (IsAuthenticated, IsOwner)
"""

from comic.models import Series
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from subscriptions.models import Subscription

User = get_user_model()


class SubscriptionAPITest(APITestCase):
    """Test suite for Subscription API custom logic."""

    def setUp(self):
        """Set up test users and series."""
        self.alice = User.objects.create_user(
            username="alice",
            email="alice@email.com",
            password="alicepassword123",
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@email.com",
            password="bobpassword123",
        )

        # Create two series
        self.series1 = Series.objects.create(
            title_tw="系列一",
            title_jp="シリーズ一",
            author_tw="作者一",
            author_jp="著者一",
        )
        self.series2 = Series.objects.create(
            title_tw="系列二",
            title_jp="シリーズ二",
            author_tw="作者二",
            author_jp="著者二",
        )

        # Create subscriptions
        Subscription.objects.create(user=self.alice, series=self.series1)
        Subscription.objects.create(user=self.bob, series=self.series2)

        self.list_url = reverse("subscription-list")

    def test_destroy_subscription_by_series(self):
        """Test that a subscription can be deleted using series ID."""
        self.client.force_authenticate(user=self.alice)

        subscription = Subscription.objects.get(user=self.alice, series=self.series1)
        response = self.client.delete(
            reverse("subscription-destroy-by-series", args=[subscription.series.id])
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subscription.objects.filter(id=subscription.id).exists())

    def test_unfollow_not_following_series(self):
        """Test that unfollowing a series the user is not following returns 404."""
        self.client.force_authenticate(user=self.alice)

        # Alice is not following series2 (Bob is following it)
        response = self.client.delete(
            reverse("subscription-destroy-by-series", args=[self.series2.id])
        )

        # Should return 404 with our custom message
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "您尚未訂閱此系列")

    def test_list_subscriptions_isolation(self):
        """Test that users only see their own subscriptions."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["series"], self.series1.id)

    def test_detail_permission_protection(self):
        """Test that users cannot access other users' subscription details."""
        self.client.force_authenticate(user=self.alice)

        # Attempt to access Bob's subscription
        bob_subscription_id = Subscription.objects.get(user=self.bob).id
        detail_url = reverse("subscription-detail", args=[bob_subscription_id])

        response = self.client.get(detail_url)
        # 404 because get_queryset filters by user, not because of IsOwner
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_subscription_automatically_assigns_user(self):
        """
        Test that user is automatically assigned from request context.

        This tests our CUSTOM serializer configuration:
        user = serializers.HiddenField(default=serializers.CurrentUserDefault())

        This prevents users from creating subscriptions for other users.
        """
        self.client.force_authenticate(user=self.alice)

        new_series = Series.objects.create(
            title_tw="系列三",
            title_jp="シリーズ三",
            author_tw="作者三",
            author_jp="著者三",
        )
        data = {
            "series": new_series.id,
            "receive_email": True,
            "receive_line": False,
        }

        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify user was auto-assigned (not from request data)
        subscription = Subscription.objects.get(id=response.data["id"])
        self.assertEqual(subscription.user, self.alice)
        self.assertEqual(subscription.series, new_series)
