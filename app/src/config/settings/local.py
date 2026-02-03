from .base import *

# ============================================================
# Development Settings - Override for Local Development
# ============================================================

DEBUG = True
SECRET_KEY = env("SECRET_KEY")

# Turn off security features for local development
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# CSRF 和 Session cookie 設定（允許跨端口通訊）
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # 讓 JavaScript 可以讀取 CSRF token
SESSION_COOKIE_SAMESITE = "Lax"

# 信任的來源（本地開發用）
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://backend:8000",
]

# 允許 Docker container 間的通訊
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend", "0.0.0.0"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", cast=int),
    }
}
