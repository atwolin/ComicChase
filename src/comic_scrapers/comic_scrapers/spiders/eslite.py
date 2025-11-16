from time import sleep
import json
import scrapy
from scrapy.http import Request, Response

from comic_scrapers.items import OrphanVolumeItem, OrphanMapItem
from comic.models import Volume

class EsliteSpider(scrapy.Spider):
    name = "eslite"
    allowed_domains = ["eslite.com"]
    start_urls = ["https://www.eslite.com/search?query="]

    def start_requests(self):
        """
        Obtain ISBN by appending isbn_tw to start parsing eslite search results page
        """
        url = self.start_urls[0]
        # data = json.load(open("orphan_test2.json", "r"))
        data = Volume.objects.filter(comic__isnull=True).values('isbn_tw')
        isbn_list = [item['isbn_tw'].strip('ISBN：') for item in data if item['isbn_tw']]
        # yield from (Request(url + isbn, callback=self.parse) for isbn in isbn_list)
        for i, isbn in enumerate(isbn_list):
            yield Request(url + isbn, callback=self.parse)
            if i == 5:  # Limit to first 5 for testing
                break

    def parse(self, response: Response):
        """
        Obtain book links from the eslite search results page and
        find the only matching link that contains the targeted ISBN
        """
        self.logger.info(f"Parsing search results from {response.url}")
        item = OrphanMapItem()
        item['isbn_tw'] = response.url.split('query=')[-1]
        item['search_url'] = response.url

        # Get book detail links
        links = response.xpath("//div[@class='item-image-link __web-inspector-hide-shortcut__']")

        yield from response.follow_all(links, callback=self.parse_book_info, meta={'item': item})


    def parse_book_info(self, response: Response):
        """
        Extract comic and volume information from the book link
        """
        self.logger.info(f"Parsing comic info from {response.url}")
        item = response.meta['item']
        detail_tw = response.xpath("//div[@id='content-998']").get()
        if not item['isbn_tw'] in detail_tw:
            yield item

        item['detail_url'] = response.url
        try:
            # Comic fields
            title_jp = response.xpath("//h4[@class='local-fw-normal font-normal text-gray-400']/text()").get()
            title_tw = response.xpath("//h1[@class='sans-font-semi-bold']/text()").get()
            author_tw = response.xpath("//div[@class='author flex mb-1']/text()").get()

            # Volume fields
            # volume_number
            release_date_tw = response.xpath("//div[@class='publicDate flex mb-1']/text()").get()
            publisher_tw = response.xpath("//div[@class='publisher flex mb-1']/a/text()").get()

            item['title_jp'] = title_jp.strip()
            item['title_tw'] = title_tw.strip()
            item['author_tw'] = author_tw.strip()
            item['release_date_tw'] = release_date_tw.strip()
            item['publisher_tw'] = publisher_tw.strip()

            self.logger.info(f"Successfully parsed comic info from {response.url}")

        except AttributeError as e:
            self.logger.error(f"Error parsing comic info from {response.url}: {e}")

        finally:
            sleep(20)
            yield item









# /html/body/div[1]/div/div[1]/div[4]/div/div[2]/div[1]/form/input
# /html/body/div[1]/div/div[3]/div[2]/div[2]/div/div[2]/div[6]/div/div/a