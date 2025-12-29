import os
import subprocess

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crawl new book releases from books.com.tw"

    def handle(self, *args, **options):
        self.stdout.write("Starting books.com.tw new releases crawl...")

        # Get the directory containing scrapy.cfg (same as manage.py)
        scrapy_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        result = subprocess.run(
            ["scrapy", "crawl", "books_tw"],
            capture_output=True,
            text=True,
            cwd=scrapy_dir,
        )

        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS("books.com.tw crawl finished."))
            # Output Scrapy stdout
            if result.stdout:
                self.stdout.write(result.stdout)
            # Output Scrapy logs (from stderr)
            if result.stderr:
                self.stderr.write(result.stderr)
        else:
            self.stderr.write(
                self.style.ERROR(f"Crawl failed with exit code {result.returncode}")
            )
            self.stderr.write("STDOUT:")
            self.stderr.write(result.stdout)
            self.stderr.write("STDERR:")
            self.stderr.write(result.stderr)
