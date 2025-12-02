from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from comic_scrapers.spiders.books_tw import BooksTWSpider


class Command(BaseCommand):
    help = "Crawl books.com.tw for orphan volumes"

    def handle(self, *args, **options):
        self.stdout.write("Starting books.com.tw crawl...")
        process = CrawlerProcess(get_project_settings())
        process.crawl(BooksTWSpider)
        process.start()
        self.stdout.write("books.com.tw crawl finished.")
