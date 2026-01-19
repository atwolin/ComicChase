import io
import os
from urllib.parse import urlparse

import environ

from .base import *

# ============================================================
# Cloud Run Production Settings
# ============================================================

# Read APPLICATION_SETTINGS environment variable
env = environ.Env()
env.read_env(io.StringIO(os.environ.get("APPLICATION_SETTINGS", "")))

# ============================================================
# Security Settings
# ============================================================

# Default false. True allows default landing pages to be visible
# DEBUG = True
# DJANGO_SECURE_SSL_REDIRECT = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================
# Django Core Settings
# ============================================================

SECRET_KEY = env("SECRET_KEY")

# ============================================================
# CORS & CSRF Settings
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:9000",
    "https://comicchase.web.app",
]
CORS_EXTRA_ORIGINS_STR = env("CORS_EXTRA_ORIGINS", default="")
if CORS_EXTRA_ORIGINS_STR:
    CORS_ALLOWED_ORIGINS.extend(
        [origin.strip() for origin in CORS_EXTRA_ORIGINS_STR.split(",")]
    )

# Enable credentials (cookies) for cross-origin requests
CORS_ALLOW_CREDENTIALS = True

# Secure=True ensures cookies are only sent over HTTPS
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True

CLOUDRUN_SERVICE_URLS = env("CLOUDRUN_SERVICE_URLS", default=None)
if CLOUDRUN_SERVICE_URLS:
    CSRF_TRUSTED_ORIGINS = [url.strip() for url in CLOUDRUN_SERVICE_URLS.split(",")]
    # Remove the scheme from URLs for ALLOWED_HOSTS
    ALLOWED_HOSTS = [urlparse(url).netloc for url in CSRF_TRUSTED_ORIGINS]
else:
    # Fail explicitly if CLOUDRUN_SERVICE_URLS is not configured
    raise ValueError("CLOUDRUN_SERVICE_URLS must be set in production")

# Add Firebase Hosting URL to CSRF trusted origins
# This is required because Firebase Hosting proxies requests to Cloud Run
# but the Origin/Referer header remains as the Firebase Hosting URL
CSRF_TRUSTED_ORIGINS.append("https://comicchase.web.app")

# ============================================================
# Database Settings
# ============================================================

# Change database settings if using the Cloud SQL Auth Proxy
if env("USE_CLOUD_SQL_AUTH_PROXY", default=False):
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = 5432

# ============================================================
# Static Files & Storage
# ============================================================

GS_BUCKET_NAME = env("GS_BUCKET_NAME", default="")

if GS_BUCKET_NAME:
    # For deployment
    STATICFILES_DIRS = []
    GS_DEFAULT_ACL = "publicRead"
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
    }
else:
    # Local filesystem storage for testing with WhiteNoise
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    # Add WhiteNoise middleware for local testing
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
