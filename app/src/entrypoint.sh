#!/bin/bash
set -e

DB_HOST=${SQL_HOST:-db}
DB_PORT=${SQL_PORT:-5432}

# Wait for database
./wait-for-it.sh "$DB_HOST:$DB_PORT" --timeout=15 --strict -- echo "Database is ready"

# Run migrations
python manage.py migrate --noinput

# Execute the main command
exec "$@"
