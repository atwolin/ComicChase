from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from comic_scrapers.spiders.eslite import EsliteISBNSpider


class Command(BaseCommand):
    help = "Crawl eslite.com for mapping orphan tw volumes"

    def handle(self, *args, **options):
        self.stdout.write("Starting eslite.com crawl using isbn...")
        process = CrawlerProcess(get_project_settings())
        process.crawl(EsliteISBNSpider)
        process.start()
        self.stdout.write("eslite.com crawl finished.")
