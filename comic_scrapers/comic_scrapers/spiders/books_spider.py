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

    def parse_volume_info(self, response: Response):
        """
        Extract volume information from the book link
        Information includes volume_number, release_date_tw, isbn_tw, publisher_tw
        """
        item = OrphanVolumeItem()
        item['source_url'] = response.url

        try:
            isbn_tw = response.xpath("//div[@class='bd']/ul/li[contains(text(), 'ISBN：')]/text()").get()

            volume_number = response.xpath("//div[@class='mod type02_p002 clearfix']/h1/text()").get()

            release_date_tw = response.xpath("//div[@class='type02_p003 clearfix']/ul/li[contains(text(), '出版日期：')]/text()").get()

            publisher_tw = response.xpath("//div[@class='type02_p003 clearfix']/ul/li[contains(text(), '出版社：')]")
            publisher_tw = publisher_tw.xpath("./a[1]/span/text()").get() if publisher_tw else None

            item['isbn_tw'] = isbn_tw
            item['volume_number'] = volume_number
            item['release_date_tw'] = release_date_tw
            item['publisher_tw'] = publisher_tw

        except AttributeError as e:
            self.logger.error(f"Error parsing volume info from {response.url}: {e}")

        finally:
            yield item
