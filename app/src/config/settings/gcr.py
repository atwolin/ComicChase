import io
import os
from urllib.parse import urlparse

import environ
from django.core.exceptions import ImproperlyConfigured

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

# IMPORTANT: Disable SSL redirect for Cloud Run
# Cloud Run handles TLS termination at the load balancer level,
# so Django should not try to redirect HTTP to HTTPS
SECURE_SSL_REDIRECT = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================
# Django Core Settings
# ============================================================

SECRET_KEY = env("SECRET_KEY")

# ============================================================
# CORS & CSRF Settings
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "https://comicchase.site",
    "https://www.comicchase.site",
    "https://api.comicchase.site",
    "https://comicchase.web.app",  # Firebase default domain (fallback)
]
CORS_EXTRA_ORIGINS_STR = env("CORS_EXTRA_ORIGINS", default="")
if CORS_EXTRA_ORIGINS_STR:
    CORS_ALLOWED_ORIGINS.extend(
        [
            origin.strip()
            for origin in CORS_EXTRA_ORIGINS_STR.split(",")
            if origin.strip()
        ]
    )

# Enable credentials (cookies) for cross-origin requests
CORS_ALLOW_CREDENTIALS = True

# Cookie settings for same root domain (comicchase.site)
# Using api.comicchase.site for Cloud Run enables cookie sharing across subdomains
# Set cookie domain to .comicchase.site to share cookies between subdomains
SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default=".comicchase.site")
CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default=".comicchase.site")

# SameSite=Lax is more secure and works for same-site requests
# (subdomains of the same root domain are considered same-site)
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True

CLOUDRUN_SERVICE_URLS = env("CLOUDRUN_SERVICE_URLS", default=None)
if CLOUDRUN_SERVICE_URLS:
    raw_urls = [u.strip() for u in CLOUDRUN_SERVICE_URLS.split(",") if u.strip()]
    CSRF_TRUSTED_ORIGINS = [u if "://" in u else f"https://{u}" for u in raw_urls]
    # Remove the scheme from URLs for ALLOWED_HOSTS
    ALLOWED_HOSTS = [urlparse(url).netloc for url in CSRF_TRUSTED_ORIGINS]
    if not all(ALLOWED_HOSTS):
        raise ImproperlyConfigured(
            "CLOUDRUN_SERVICE_URLS must contain full URLs with scheme"
        )
else:
    raise ImproperlyConfigured("CLOUDRUN_SERVICE_URLS is required for Cloud Run")

# CRITICAL: Tell Django to use the X-Forwarded-Host header
# This ensures django-allauth generates URLs with the correct domain
# Without this, session cookies will be set for the wrong domain, causing 409 errors
USE_X_FORWARDED_HOST = True

# ============================================================
# Database Settings
# ============================================================

# Use DATABASE_URL for Cloud Run
DATABASES = {"default": env.db()}

# Change database settings if using the Cloud SQL Auth Proxy
if env.bool("USE_CLOUD_SQL_AUTH_PROXY", default=False):
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = 5432

# ============================================================
# Static Files & Storage
# ============================================================

GS_BUCKET_NAME = env("GS_BUCKET_NAME", default="")
ALLOW_LOCAL_STORAGE = env.bool("ALLOW_LOCAL_STORAGE", default=False)

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
elif ALLOW_LOCAL_STORAGE:
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
    if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
        MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
else:
    raise ValueError(
        "GS_BUCKET_NAME must be set for Cloud Run storage, "
        "or set ALLOW_LOCAL_STORAGE=true for local testing"
    )

# ============================================================
# AWS Federation Settings (for SES Email)
# ============================================================

# When True, use Google-to-AWS Workload Identity Federation
# instead of static AWS Access Keys
AWS_USE_FEDERATION = env.bool("AWS_USE_FEDERATION", default=True)
AWS_ROLE_ARN = env("AWS_ROLE_ARN", default="")

# ============================================================
# Email Settings
# ============================================================

# Override DEFAULT_FROM_EMAIL from base.py with Secret Manager value
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@comicchase.site")
