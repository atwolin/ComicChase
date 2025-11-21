from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from comic_scrapers.spiders.books_jp import BooksJpTitleTwSpider


class Command(BaseCommand):
    help = "Crawl book titles from books.or.jp to update Japanese comic titles"

    def handle(self, *args, **options):
        self.stdout.write("Starting books.or.jp title crawl using existing jp titles...")
        process = CrawlerProcess(get_project_settings())
        process.crawl(BooksJpTitleTwSpider)
        process.start()
        self.stdout.write("books.or.jp title crawl completed.")
