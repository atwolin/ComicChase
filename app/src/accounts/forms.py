from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Auto-generate username from email if not provided
        if not user.username:
            user.username = user.email.split("@")[0]
            # Ensure uniqueness by appending a number if needed
            base_username = user.username
            counter = 1
            while get_user_model().objects.filter(username=user.username).exists():
                user.username = f"{base_username}{counter}"
                counter += 1
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ("email",)
