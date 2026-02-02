import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Search and crawl volumes from eslite.com by title"

    def add_arguments(self, parser):
        parser.add_argument(
            "--title",
            type=str,
            required=True,
            help='Series title to crawl (e.g., "排球少年", "藍色時期")',
        )
        parser.add_argument(
            "--last-release-date",
            type=str,
            help="Last release date in YYYY-MM-DD format",
        )

    def handle(self, *args, **options):
        title = options.get("title")
        last_date = options.get("last_release_date")

        cmd = ["scrapy", "crawl", "eslite_title_tw"]
        cmd.extend(["-a", f"search_value={title}"])

        # Only pass last_release_date if it has a value
        # to avoid passing string "None" instead of Python None
        if last_date:
            cmd.extend(["-a", f"last_release_date={last_date}"])

        # Get the directory containing scrapy.cfg (BASE_DIR from settings)
        scrapy_dir = str(settings.BASE_DIR)

        self.stdout.write(f"Starting eslite.com title search for: {title}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=scrapy_dir)
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR("'scrapy' command not found. Is Scrapy installed?")
            )
            raise CommandError("Scrapy not found")

        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS("eslite.com crawl finished."))
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
