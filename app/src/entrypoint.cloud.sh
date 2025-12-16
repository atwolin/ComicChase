#!/bin/bash
set -e

# For Cloud Run, database connection is handled via Cloud SQL Proxy (Unix socket)
# No need to wait for TCP connection like in local development

# Set Django settings for Cloud environment
export DJANGO_SETTINGS_MODULE=config.settings.cloud

# Collect static files (uploaded to GCS bucket)
python manage.py collectstatic --noinput

# Execute the main command
exec "$@"
