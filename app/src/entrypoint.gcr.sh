#!/bin/bash
set -e

# Set Django settings for Cloud environment
export DJANGO_SETTINGS_MODULE=config.settings.gcr

# For local testing, wait for database if DB_HOST is provided
# In production Cloud Run, this is skipped (Cloud SQL uses Unix socket)
if [ -n "$DB_HOST" ]; then
    DB_PORT=${DB_PORT:-5432}

    # Wait for database
    ./wait-for-it.sh "$DB_HOST:$DB_PORT" --timeout=15 --strict -- echo "Database is ready"

    # Run migrations for local testing
    # Note: In production, migrations are run via Cloud Run Jobs (see cloudmigrate.yaml)
    python manage.py migrate --noinput

    # Collect static files for local testing
    python manage.py collectstatic --noinput
fi

# Execute the main command
exec "$@"
