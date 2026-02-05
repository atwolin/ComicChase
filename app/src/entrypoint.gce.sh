#!/bin/bash
set -e

# Wait for database
./wait-for-it.sh "$DB_HOST:$DB_PORT" --timeout=15 --strict -- echo "Database is ready"

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Execute the main command
exec "$@"
