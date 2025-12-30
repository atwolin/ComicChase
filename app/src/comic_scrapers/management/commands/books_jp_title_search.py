import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Search and crawl Japanese comic titles from books.or.jp"

    def add_arguments(self, parser):
        parser.add_argument(
            "--title",
            type=str,
            help="Series title in Japanese to crawl",
        )
        parser.add_argument(
            "--last-release-date",
            type=str,
            help="Last release date in YYYY-MM-DD format",
        )

    def handle(self, **options):
        title = options.get("title")
        last_date = options.get("last_release_date")

        cmd = ["scrapy", "crawl", "booksjp_title"]

        if title:
            self.stdout.write(f"Starting books.or.jp title search for: {title}")
            cmd.extend(["-a", f"search_value={title}"])
            if last_date:
                cmd.extend(["-a", f"last_release_date={last_date}"])
        else:
            self.stdout.write("Starting books.or.jp title search for all series...")

        # Get the directory containing scrapy.cfg (BASE_DIR from settings)
        scrapy_dir = str(settings.BASE_DIR)

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=scrapy_dir)

        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS("books.or.jp crawl completed."))
            if result.stdout:
                self.stdout.write(result.stdout)
            if result.stderr:
                self.stderr.write(result.stderr)
        else:
            self.stderr.write(
                self.style.ERROR(f"Crawl failed with exit code {result.returncode}")
            )
            self.stderr.write("STDOUT:")
            self.stdout.write(result.stdout)
            self.stderr.write("STDERR:")
            self.stderr.write(result.stderr)
