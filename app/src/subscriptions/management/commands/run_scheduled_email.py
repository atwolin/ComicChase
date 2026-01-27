"""
Django management command to run scheduled email notification tasks.

This command integrates with Cloud Run Jobs for serverless execution.
"""

import logging
import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from subscriptions.tasks import run_weekly_notification_flow

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run scheduled email notification tasks for Cloud Run Jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task",
            type=str,
            required=True,
            help="Task name to execute (e.g., 'weekly_digest')",
        )

    def handle(self, *args, **options):
        task_name = options["task"]
        start_time = datetime.now()

        self.stdout.write("=" * 80)
        self.stdout.write("Cloud Run Email Notification Job")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Task: {task_name}")
        self.stdout.write(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        self.stdout.write("=" * 80)

        try:
            if task_name == "weekly_digest":
                self.stdout.write(
                    self.style.SUCCESS("📧 Running weekly digest email notification...")
                )
                self.stdout.write("=== Starting scheduled task: weekly_digest ===")

                # 執行同步模式（sync=True）用於 Cloud Run Jobs
                result = run_weekly_notification_flow(sync=True)

                self.stdout.write(self.style.SUCCESS(f"✅ Result: {result}"))
                self.stdout.write("=== Completed scheduled task: weekly_digest ===")

            else:
                self.stderr.write(
                    self.style.ERROR(f"❌ Error: Unknown EMAIL_TASK: {task_name}")
                )
                self.stderr.write("Valid tasks: weekly_digest")
                sys.exit(1)

            # 完成訊息
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.stdout.write("=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ Email Notification Job Completed"))
            self.stdout.write(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            self.stdout.write(f"Duration: {duration:.2f} seconds")
            self.stdout.write("=" * 80)

        except Exception as e:
            self.stderr.write("=" * 80)
            self.stderr.write(self.style.ERROR("❌ Email Notification Job Failed"))
            self.stderr.write(f"Error: {str(e)}")
            self.stderr.write("=" * 80)
            logger.exception(f"Email task {task_name} failed")
            sys.exit(1)
