from .base import *

# Security
SECRET_KEY = config("SECRET_KEY")
CSRF_COOKIE_SECURE = True  # Ensure CSRF cookies are only sent over HTTPS
SESSION_COOKIE_SECURE = True  # Ensure session cookies are only sent over HTTPS
SECURE_SSL_REDIRECT = True  # Redirect all HTTP requests to HTTPS
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # Trust X-Forwarded-Proto from Nginx
# SECURE_HSTS_SECONDS = 3600 # Enable HTTP Strict Transport Security (HSTS)

DEBUG = False

ADMINS = [("atwolin", "tzhuchien@nlplab.cc")]

# TODO: Update with actual production hosts
ALLOWED_HOSTS = ["comicchase.com.tw"]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    "http://comicchase.com.tw",
    "https://comicchase.com.tw",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="comic_db"),
        "USER": config("POSTGRES_USER", default="comic_user"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="comic_pass"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default=5432, cast=int),
    }
}
