from rest_framework import serializers

from .models import CustomUser


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "receive_email")
        read_only_fields = ("id", "email")
