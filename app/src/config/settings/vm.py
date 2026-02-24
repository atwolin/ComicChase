from .base import *

# ============================================================
# VM Production Settings (Firebase Frontend)
# ============================================================

# Inherit from base settings includes
# - DEBUG = False
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
SECRET_KEY = env("SECRET_KEY")
ADMINS = [("atwolin", "tzhuchien@nlplab.cc")]

# ============================================================
# Host Configuration
# ============================================================

ALLOWED_HOSTS = [
    "comicchase.site",  # Firebase Hosting
    "api.comicchase.site",  # GCE API domain
]

# ============================================================
# CORS & CSRF Settings
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "https://comicchase.site",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.site",
]

# Cookie settings for cross-subdomain authentication
# Frontend (comicchase.site) and API (api.comicchase.site) share cookies
SESSION_COOKIE_DOMAIN = ".comicchase.site"
CSRF_COOKIE_DOMAIN = ".comicchase.site"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True

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
