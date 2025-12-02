from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from comic_scrapers.spiders.eslite import EsliteTitleTwSpider


class Command(BaseCommand):
    help = "Crawl eslite.com for searching volumes for each series by title"

    def add_arguments(self, parser):
        parser.add_argument(
            "--series-name",
            type=str,
            help='Series name to crawl (e.g., "排球少年", '
            '"迴天的阿爾帕斯", "藍色時期", etc.)',
        )

    def handle(self, *args, **options):
        series_name = options.get("series_name")
        process = CrawlerProcess(get_project_settings())

        if series_name:
            self.stdout.write(f"Starting eslite.com crawl for series: {series_name}")
            process.crawl(EsliteTitleTwSpider, topic_list=[series_name])
        else:
            self.stdout.write("Starting eslite.com crawl using title...")
            process.crawl(EsliteTitleTwSpider)

        process.start()
        self.stdout.write("eslite.com crawl finished.")
