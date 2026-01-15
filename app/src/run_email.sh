#!/bin/bash
# Shell script to run email notification tasks in Cloud Run Jobs
# This script is called by Cloud Run Jobs with the EMAIL_TASK environment variable

set -e  # Exit on any error

# 確保在正確的目錄（Docker container 中 manage.py 在 /code/app）
cd /code/app

# 檢查必要的環境變數
if [ -z "$EMAIL_TASK" ]; then
    echo "❌ Error: EMAIL_TASK environment variable is not set"
    echo "Available tasks:"
    echo "  - weekly_digest: Send weekly comic digest emails"
    exit 1
fi

echo "==========================================="
echo "Starting Email Notification Task"
echo "==========================================="
echo "Task: $EMAIL_TASK"
echo "Time: $(date)"
echo "==========================================="

# 執行 Django management command
python manage.py run_scheduled_email --task "$EMAIL_TASK"

# 檢查執行結果
if [ $? -eq 0 ]; then
    echo "==========================================="
    echo "✅ Email Task Completed Successfully"
    echo "Task: $EMAIL_TASK"
    echo "Time: $(date)"
    echo "==========================================="
    exit 0
else
    echo "==========================================="
    echo "❌ Email Task Failed"
    echo "Task: $EMAIL_TASK"
    echo "Time: $(date)"
    echo "==========================================="
    exit 1
fi
