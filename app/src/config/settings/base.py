from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

env = environ.Env(
    # Security Settings (Production-safe defaults)
    DEBUG=(bool, False),
    DJANGO_SECURE_SSL_REDIRECT=(bool, True),
    DJANGO_CSRF_COOKIE_SECURE=(bool, True),
    DJANGO_SESSION_COOKIE_SECURE=(bool, True),
    DJANGO_SECURE_HSTS_SECONDS=(int, 31536000),  # 1 year
    DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, True),
    DJANGO_SECURE_HSTS_PRELOAD=(bool, True),
)
env.read_env()

# ==========================================================
# Security Settings (Secure by Default)
# ==========================================================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="django-insecure-test-key-for-development-only")

# HTTPS/SSL Settings
SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT")
# CSRF_COOKIE_SECURE = env("DJANGO_CSRF_COOKIE_SECURE")
# SESSION_COOKIE_SECURE = env("DJANGO_SESSION_COOKIE_SECURE")

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = env("DJANGO_SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = env("DJANGO_SECURE_HSTS_PRELOAD")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# ==========================================================
# Application definition
# ==========================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_celery_results",
    "django_ses",
    "rest_framework",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.usersessions",
    "corsheaders",
    "drf_spectacular",
    "apis.apps.ApisConfig",
    "accounts.apps.AccountsConfig",
    "comic.apps.ComicConfig",
    "subscriptions.apps.SubscriptionsConfig",
    "comic_scrapers.apps.ComicScrapersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "zh-TW"

TIME_ZONE = "Asia/Taipei"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/django-static/"
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.CustomUser"

# ============================================================
# django-allauth config
# ============================================================
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# Account config
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_VERIFICATION = "optional"  # TODO: set "mandatory" after email setup
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False
# ACCOUNT_LOGIN_BY_CODE_ENABLED = True
# ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]

HEADLESS_ONLY = True
# Frontend URL for email links
FRONTEND_URL = env("FRONTEND_URL", default="https://comicchase.site")
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{FRONTEND_URL}/account/verify-email/{{key}}",
    "account_reset_password": f"{FRONTEND_URL}/account/password/reset",
    "account_reset_password_from_key": (
        f"{FRONTEND_URL}/account/password/reset/key/{{key}}"
    ),
    "account_signup": f"{FRONTEND_URL}/account/signup",
    "socialaccount_login_error": f"{FRONTEND_URL}/account/provider/callback",
}
HEADLESS_SERVE_SPECIFICATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = env("ACCOUNT_DEFAULT_HTTP_PROTOCOL", default="https")

# ============================================================
# CORS Settings (for local development)
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF config
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ============================================================
# Email settings
# ============================================================
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@comicchase.local")

# AWS SES Configuration: Django-SES specific settings
AWS_SES_REGION_NAME = env("AWS_SES_REGION_NAME", default="ap-northeast-1")
AWS_SES_REGION_ENDPOINT = env(
    "AWS_SES_REGION_ENDPOINT", default="email.ap-northeast-1.amazonaws.com"
)

# Boto3 requires this for proper credential scoping
AWS_DEFAULT_REGION = env("AWS_DEFAULT_REGION", default="ap-northeast-1")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default=None)

# Use SES v1 API (more stable)
USE_SES_V2 = False

# ============================================================
# Celery Configuration
# ============================================================
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://")
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # 1 day

# Reliability for RabbitMQ
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Worker
CELERY_WORKER_MAX_TASKS_PER_CHILD = 2
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Serializer
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Asia/Taipei"
CELERY_ENABLE_UTC = True

# Router
CELERY_TASK_ROUTES = (
    [
        ("comic_scrapers.tasks.*", {"queue": "crawler"}),
    ],
)

# ============================================================
# django-rest-framework config
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

# ============================================================
# drf-spectacular config
# ============================================================
SPECTACULAR_SETTINGS = {
    "TITLE": "ComicChase API",
    "DESCRIPTION": "API for ComicChase application",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "EXTERNAL_DOCS": {"description": "allauth", "url": "/_allauth/openapi.html"},
}
