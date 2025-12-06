from .base import *

DEBUG = True

import sys  # noqa: E402

# Use separate database backends:
# - SQLite for unit tests (faster, isolated)
# - PostgreSQL for development and production
if "test" in sys.argv or "pytest" in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
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
