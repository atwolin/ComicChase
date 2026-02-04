import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserPreferenceSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class UserPreferenceView(APIView):
    """
    API endpoint to get/set user preferences (receive_email).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserPreferenceSerializer})
    def get(self, request):
        # Serializer handles fetching fresh data
        serializer = UserPreferenceSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=UserPreferenceSerializer,
        responses={200: UserPreferenceSerializer},
    )
    def patch(self, request):
        serializer = UserPreferenceSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            # Before save logging
            old_val = request.user.receive_email

            serializer.save()

            # After save logging
            new_val = serializer.instance.receive_email
            logger.info(
                "[Preference] User id=%s updated receive_email: %s -> %s",
                request.user.id,
                old_val,
                new_val,
            )
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


class UnsubscribeView(APIView):
    """
    Handle email unsubscribe requests via API (Headless).

    GET: Validate token and return user info (for confirmation UI).
    POST: Execute unsubscribe action.

    Query Params / Body:
        token: User's unsubscribe_token (UUID)
    """

    permission_classes = [AllowAny]

    def get_user_by_token(self, token):
        if not token:
            return None
        try:
            return User.objects.get(unsubscribe_token=token)
        except (User.DoesNotExist, ValueError, ValidationError):
            return None

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                description="User's unsubscribe token (UUID)",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request):
        token = request.query_params.get("token")
        user = self.get_user_by_token(token)

        if not user:
            return Response({"detail": "Invalid or missing token."}, status=400)

        return Response(
            {
                "email": user.email,
                "status": "valid",
                "message": "Token is valid. Proceed to unsubscribe.",
            }
        )

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "User's unsubscribe token",
                    }
                },
                "required": ["token"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "email": {"type": "string"},
                },
            },
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def post(self, request):
        token = request.data.get("token")
        user = self.get_user_by_token(token)

        if not user:
            return Response({"detail": "Invalid or missing token."}, status=400)

        # Disable global email notifications
        user.receive_email = False
        user.save(update_fields=["receive_email"])

        logger.info("[Unsubscribe] Disabled global email for user_id=%s", user.id)

        return Response(
            {
                "status": "success",
                "message": "Successfully unsubscribed.",
                "email": user.email,
            }
        )
