import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Search and crawl volumes from eslite.com by ISBN"

    def add_arguments(self, parser):
        parser.add_argument(
            "--isbn",
            type=str,
            required=True,
            help="ISBN to search for",
        )

    def handle(self, *args, **options):
        isbn = options.get("isbn")

        cmd = ["scrapy", "crawl", "eslite_isbn"]
        cmd.extend(["-a", f"search_value={isbn}"])

        # Get the directory containing scrapy.cfg (BASE_DIR from settings)
        scrapy_dir = str(settings.BASE_DIR)

        self.stdout.write(f"Starting eslite.com ISBN search for: {isbn}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=scrapy_dir)

        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS("eslite.com ISBN search finished."))
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
