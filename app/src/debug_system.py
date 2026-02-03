import os

import django

# Initialize Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.gcr")
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402


def run_diagnostics():
    print("=== SYSTEM DIAGNOSTICS ===")

    # 1. Database Configuration
    print("\n[Database Config]")
    db = settings.DATABASES["default"]
    print(f"Engine: {db['ENGINE']}")
    print(f"Name: {db['NAME']}")
    # Mask password but show host
    print(f"Host: {db.get('HOST', 'Not Set')}")
    print(f"Port: {db.get('PORT', 'Not Set')}")

    # 2. User Inspection
    User = get_user_model()
    target_email = "amelia322468@gmail.com"
    print(f"\n[User Inspection] Searching for: {target_email}")

    users = User.objects.filter(email=target_email)
    count = users.count()
    print(f"Found {count} user(s) with this email.")

    for u in users:
        print("---")
        print(f"ID: {u.pk}")
        print(f"Username: {u.username}")
        print(f"Email: {u.email}")
        print(f"Receive Email: {u.receive_email}")
        print(f"Is Active: {u.is_active}")

    print("\n=== END DIAGNOSTICS ===")


if __name__ == "__main__":
    run_diagnostics()
