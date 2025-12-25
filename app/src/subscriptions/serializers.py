from rest_framework import serializers, validators

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user",
            "series",
            "receive_email",
            "receive_line",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

        validators = [
            # Prevents a user from subscribing to the same series multiple times
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=["user", "series"],
                message="您已經訂閱過此系列了。",
            ),
        ]
