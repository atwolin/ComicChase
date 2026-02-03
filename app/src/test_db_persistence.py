import os

import django

# Initialize Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.gcr")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()
email = "[EMAIL_ADDRESS]"

try:
    user = User.objects.get(email=email)
    print(f"Current value: {user.receive_email}")

    print("Setting to False...")
    user.receive_email = False
    user.save()

    # Re-fetch
    user.refresh_from_db()
    print(f"Value after save and refresh: {user.receive_email}")

    if user.receive_email is False:
        print("SUCCESS: Database persistence works.")
    else:
        print("FAILURE: Database Persistence reverted the value!")

except User.DoesNotExist:
    print(f"User {email} not found!")
