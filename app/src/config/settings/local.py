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
