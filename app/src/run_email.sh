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
    echo "  - test_email: Send a test email (requires TEST_EMAIL_TO)"
    exit 1
fi

echo "==========================================="
echo "Starting Email Notification Task"
echo "==========================================="
echo "Task: $EMAIL_TASK"
echo "Time: $(date)"
echo "==========================================="

# 根據任務類型執行不同的命令
case "$EMAIL_TASK" in
    "weekly_digest")
        echo "📧 Running weekly digest email notification..."
        python manage.py run_scheduled_email --task "$EMAIL_TASK"
        ;;
    "test_email")
        # 檢查測試郵件收件人
        if [ -z "$TEST_EMAIL_TO" ]; then
            echo "❌ Error: TEST_EMAIL_TO environment variable is required for test_email task"
            echo "Example: TEST_EMAIL_TO=your@email.com"
            exit 1
        fi
        echo "📧 Sending test email to: $TEST_EMAIL_TO"
        python manage.py send_test_email --to "$TEST_EMAIL_TO"
        ;;
    *)
        echo "❌ Error: Unknown EMAIL_TASK: $EMAIL_TASK"
        echo "Available tasks:"
        echo "  - weekly_digest: Send weekly comic digest emails"
        echo "  - test_email: Send a test email (requires TEST_EMAIL_TO)"
        exit 1
        ;;
esac

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
