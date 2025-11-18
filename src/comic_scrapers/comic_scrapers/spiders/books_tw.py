import re
from time import sleep
import scrapy
from scrapy.http import Request, Response

from comic_scrapers.items import OrphanVolumeItem


class BooksTWSpider(scrapy.Spider):
    name = "books_tw"
    allowed_domains = ["books.com.tw"]
    start_urls = [
        "https://www.books.com.tw/web/sys_compub/books/16/?loc=P_0001_017",
    ]

    def parse(self, response: Response):
        """
        Obtain 100 book links from the books.com.tw new releases page
        """
        links = response.xpath("//div[@class='type02_bd-a']/h4/a/@href").getall()
        self.logger.info(f"Found {len(links)} book links on the page.")
        yield from response.follow_all(links, self.parse_volume_info)

    def parse_volume_info(self, response: Response):
        """
        Extract volume information from the book link
        Information includes volume_number, release_date_tw, isbn_tw, publisher_tw
        """
        item = OrphanVolumeItem()
        item['source_url'] = response.url

        try:
            isbn_tw = response.xpath("//div[@class='bd']/ul/li[contains(text(), 'ISBN：')]/text()").get()
            isbn_tw = isbn_tw.replace('ISBN：', '').strip() if isbn_tw else None

            item['isbn_tw'] = isbn_tw

            self.logger.info(f"Successfully parsed volume ISBN from {response.url}")

        except AttributeError as e:
            self.logger.error(f"Error parsing volume info from {response.url}: {e}")

        finally:
            sleep(20)
            yield item
