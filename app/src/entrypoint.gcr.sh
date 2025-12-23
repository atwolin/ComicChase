#!/bin/bash
set -e

# Set Django settings for Cloud environment
export DJANGO_SETTINGS_MODULE=config.settings.gcr

# For local testing, wait for database if SQL_HOST is provided
# In production Cloud Run, this is skipped (Cloud SQL uses Unix socket)
if [ -n "$SQL_HOST" ]; then
    DB_HOST=${SQL_HOST:-db}
    DB_PORT=${SQL_PORT:-5432}

    # Wait for database
    ./wait-for-it.sh "$DB_HOST:$DB_PORT" --timeout=15 --strict -- echo "Database is ready"
fi

# Run migrations
# Note: In production, migrations are run via Cloud Run Jobs (see cloudmigrate.yaml)
# For local testing, we run them here
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Execute the main command
exec "$@"
