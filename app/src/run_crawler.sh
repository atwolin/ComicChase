#!/bin/bash

# Script to run crawler tasks in Cloud Run Jobs

set -e

echo "========================================="
echo "Cloud Run Crawler Job"
echo "========================================="
echo "Task: ${CRAWLER_TASK}"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "========================================="

# Check necessary environment variables are set
if [ -z "${CRAWLER_TASK}" ]; then
    echo "Error: CRAWLER_TASK environment variable is not set"
    exit 1
fi

# Run crawler task based on CRAWLER_TASK environment variable
case ${CRAWLER_TASK} in
    "bookstw_new")
        python manage.py run_scheduled_crawler --task bookstw_new
        ;;
    "eslite_all_series")
        python manage.py run_scheduled_crawler --task eslite_all_series
        ;;
    "eslite_orphan_volumes")
        python manage.py run_scheduled_crawler --task eslite_orphan_volumes
        ;;
    "booksjp_all_series")
        python manage.py run_scheduled_crawler --task booksjp_all_series
        ;;
    *)
        echo "Error: Invalid CRAWLER_TASK environment variable"
        echo "Available tasks:"
        echo "  - bookstw_new"
        echo "  - eslite_all_series"
        echo "  - eslite_orphan_volumes"
        echo "  - booksjp_all_series"
        exit 1
        ;;
esac

echo "========================================="
echo "Crawler Job Completed"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "========================================="
