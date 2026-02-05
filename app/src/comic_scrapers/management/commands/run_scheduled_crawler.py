"""
Management command to run scheduled crawler tasks for Cloud Run Jobs.

This command provides a unified interface to execute different crawler tasks
by calling the corresponding Celery task functions synchronously (without workers).
"""

import logging

from django.core.management.base import BaseCommand

from comic_scrapers import tasks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Run scheduled crawler tasks for Cloud Run Jobs."""

    help = "Run scheduled crawler tasks for Cloud Run Jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task",
            type=str,
            choices=[
                "bookstw_new",
                "eslite_all_series",
                "eslite_orphan_volumes",
                "booksjp_all_series",
            ],
            required=True,
            help="Which crawler task to run",
        )

    def handle(self, *args, **options):
        task_name = options["task"]

        self.stdout.write(f"=== Starting scheduled task: {task_name} ===")
        logger.info(f"Starting scheduled task: {task_name}")

        try:
            if task_name == "bookstw_new":
                async_result = tasks.crawl_new_volumes_bookstw.apply()
                result = async_result.get()
            elif task_name == "eslite_all_series":
                result = tasks.crawl_all_series_eslite(sync=True)
            elif task_name == "eslite_orphan_volumes":
                result = tasks.crawl_orphan_volumes_eslite(sync=True)
            elif task_name == "booksjp_all_series":
                result = tasks.crawl_all_series_booksjp(sync=True)

            logger.info(f"Task completed: {result}")
            self.stdout.write(self.style.SUCCESS(f"✅ Completed: {task_name}"))
            self.stdout.write(f"Result: {result}")

        except Exception as e:
            logger.exception(f"Task failed: {task_name}")
            self.stderr.write(self.style.ERROR(f"❌ Failed: {task_name}"))
            self.stderr.write(str(e))
            raise
