import scrapy
import re
from scrapy.http import Request, Response

from comic_scrapers.items import OrphanVolumeItem

class BooksSpider(scrapy.Spider):
    name = "books_com"

    start_urls = [
        "https://www.books.com.tw/web/sys_compub/books/16/?loc=P_0001_017",
    ]

    def parse(self, response: Response):
        """
        Obtain 100 book links from the books.com.tw new releases page
        """
        links = response.xpath("//div[@class='type02_bd-a']/h4/a/@href").getall()
        self.logger.info(f"Found {len(links)} book links on the page.")
        # yield from response.follow_all(links, self.parse_volume_info)
        for link in links:
            yield Request(url=link, callback=self.parse_volume_info)
            break  # For testing, remove this line to scrape all links
