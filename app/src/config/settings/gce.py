from .base import *

# ============================================================
# GCE Production Settings (Firebase Frontend)
# ============================================================

# Inherit from base settings includes
# - DEBUG = False
# - SECRET_KEY = env("SECRET_KEY")
# - SECURE_SSL_REDIRECT = True
# - CSRF_COOKIE_SECURE = True
# - SESSION_COOKIE_SECURE = True
# - SECURE_HSTS_* = True

# ============================================================
# Security Settings
# ============================================================
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # Trust X-Forwarded-Proto from Nginx

ADMINS = [("atwolin", "tzhuchien@nlplab.cc")]

# ============================================================
# Host Configuration
# ============================================================

ALLOWED_HOSTS = [
    "comicchase.web.app",  # Firebase Hosting
]

# ============================================================
# CORS & CSRF Settings
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "https://comicchase.web.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.web.app",
]

# ============================================================
# Database Settings
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}
