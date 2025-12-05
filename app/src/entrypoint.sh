#!/bin/bash
set -e

# Wait for database
./wait-for-it.sh db:5432 --timeout=15 --strict -- echo "Database is ready"

# Run migrations
python manage.py migrate --noinput

# Execute the main command
exec "$@"
