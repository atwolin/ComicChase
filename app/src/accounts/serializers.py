from dj_rest_auth.serializers import UserDetailsSerializer

from .models import CustomUser


class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        model = CustomUser
        fields = UserDetailsSerializer.Meta.fields + ("receive_email",)
