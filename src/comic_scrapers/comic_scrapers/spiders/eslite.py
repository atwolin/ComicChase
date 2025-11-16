from time import sleep
import json
import scrapy
from scrapy.http import Request, Response
from asgiref.sync import sync_to_async

from comic_scrapers.items import OrphanVolumeItem, OrphanMapItem
from comic.models import Volume

class EsliteSpider(scrapy.Spider):
    name = "eslite"
    allowed_domains = ["eslite.com"]
    start_urls = ["https://www.eslite.com"]

    def start_requests(self):
        """
        Passing URL via meta to avoid linting errors
        """
        url = self.start_urls[0]
        yield scrapy.Request(url=url, callback=self.parse, meta={'url': url})

    @sync_to_async
    def parse(self, response: Response):
        """
        Generate search results URL for each ISBN and yield request to parse detail page link
        """
        url = response.meta['url']

        # Get list of ISBNs from Volume table where entry is missing associated comic
        isbn_queryset = Volume.objects.filter(comic__isnull=True).values_list('isbn_tw', flat=True)
        links = [f"{url}/search?query={isbn}" for isbn in isbn_queryset]

        # yield from response.follow_all(isbn_list, callback=self.parse_detail_page_link)
        # Test
        for i, link in enumerate(links):
            yield scrapy.Request(url=link, callback=self.parse_detail_urls)
            if i == 5:
                break


    def parse_detail_urls(self, response: Response):
        """
        Obtain book URLs from the search results URL and
        find the only matching URL that contains the targeted ISBN
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
        Extract comic and volume information from the book URL
        """
        self.logger.info(f"Parsing comic info from {response.url}")
        item = response.meta['item']

        # Check if the ISBN exists in the detail page or if it's an EPUB version
        detail_tw = response.xpath("//div[@id='content-998']").get()
        if not item['isbn_tw'] in detail_tw or 'EPUB' in detail_tw:
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
