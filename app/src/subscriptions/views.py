from apis.permissions import IsOwner
from comic.models import Series
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Subscription
from .serializers import SubscriptionSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows subscriptions to be viewed or edited.

    Standard REST endpoints:
    - GET    /api/subscriptions/              - List user's subscriptions
    - POST   /api/subscriptions/              - Follow a series
    - GET    /api/subscriptions/{id}/         - Get subscription details
    - PATCH  /api/subscriptions/{id}/         - Update notification preferences
    - DELETE /api/subscriptions/{id}/         - Unfollow (using subscription ID)

    Convenience endpoint:
    - DELETE /api/subscriptions/by-series/{series_id}/  - Unfollow (using series ID)
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        This view should return a list of all the subscriptions
        for the currently authenticated user.
        """
        return Subscription.objects.filter(user=self.request.user)

    @action(
        detail=False,
        methods=["delete"],
        url_path="by-series/(?P<series_id>[^/.]+)",
        permission_classes=[permissions.IsAuthenticated],
    )
    def destroy_by_series(self, request, series_id=None):
        """
        Unfollow a series using series ID instead of subscription ID.

        DELETE /api/subscriptions/by-series/{series_id}/

        This is a convenience method that allows unfollowing without
        knowing the subscription ID. The standard DELETE endpoint using
        subscription ID is still available and preferred when the ID is known.
        """
        # Validate that the series exists
        get_object_or_404(Series, pk=series_id)

        deleted_count, _ = self.get_queryset().filter(series_id=series_id).delete()

        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"message": "您尚未訂閱此系列"}, status=status.HTTP_404_NOT_FOUND
            )
