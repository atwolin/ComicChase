from .base import *

# ============================================================
# Development Settings - Override for Local Development
# ============================================================

DEBUG = True

# Turn off security features for local development
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="comic_db"),
        "USER": env("POSTGRES_USER", default="comic_user"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="comic_pass"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default=5432, cast=int),
    }
}
