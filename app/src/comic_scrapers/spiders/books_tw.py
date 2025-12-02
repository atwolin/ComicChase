import time

import scrapy
from scrapy.http import Response

from comic_scrapers.items import OrphanVolumeItem


class BooksTWSpider(scrapy.Spider):
    """Spider to scrape book information from books.com.tw Taiwan site.

    This spider targets the new releases section to obtain book urls
    and extracts volume information such as ISBN, release date, and publisher.
    """

    name = "books_tw"
    allowed_domains = ["books.com.tw"]
    start_urls = [
        "https://www.books.com.tw/web/sys_compub/books/16/?loc=P_0001_017",
    ]

    # Custom settings for this spider
    custom_settings = {
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 522, 524, 408, 429, 484],
    }

    def parse(self, response: Response):
        """Parse the new releases page to obtain book urls.

        Args:
            response (Response): Response object of the new releases page.

        Yields:
            Request: Follow-up requests to parse individual volume pages.

        Raises:
            Exception: If any error occurs during parsing.
        """
        try:
            self.logger.info(f"Parsing Books.com.tw Taiwan page: {response.url}")
            urls = response.xpath("//div[@class='type02_bd-a']/h4/a/@href").getall()
            self.logger.info(f"Found {len(urls)} book urls on the page.")
            yield from response.follow_all(urls, self.parse_volume_info)

        except Exception as e:
            self.logger.error(
                f"Failed to parse: {response.url}, error: {str(e)}", exc_info=True
            )

    def parse_volume_info(self, response: Response):
        """Parse the book volume page to extract volume ISBN.

        Extracts the ISBN from the book detail page to create an OrphanVolumeItem,
        which is then yielded for storing into the Volume database.

        Args:
            response (Response): Response object of the book volume page.

        Yields:
            OrphanVolumeItem: Item containing the extracted volume information.

        Raises:
            AttributeError: If expected HTML elements are not found during parsing.
            Exception: If any other error occurs during parsing.
        """
        item = OrphanVolumeItem()
        item["source_url"] = response.url

        try:
            if response.xpath(
                "//div[@class='bd']/ul/li[contains(text(), 'EISBN：')]/text()"
            ).get():
                self.logger.info(f"Skipping EPUB volume: {response.url}")
            else:
                self.logger.info(f"Parsing volume info: {response.url}")
                isbn_tw = response.xpath(
                    "//div[@class='bd']/ul/li[contains(text(), 'ISBN：')]/text()"
                ).get()
                isbn_tw = isbn_tw.replace("ISBN：", "").strip() if isbn_tw else None

                item["isbn_tw"] = isbn_tw
                if isbn_tw:
                    self.logger.info(
                        f"Successfully parsed volume ISBN {isbn_tw} from {response.url}"
                    )
                else:
                    self.logger.warning(f"No ISBN found on {response.url}")

        except AttributeError as e:
            self.logger.error(f"Error parsing volume info from {response.url}: {e}")
        except Exception as e:
            self.logger.error(
                f"Failed to parse volume: {response.url}," f"error: {str(e)}",
                exc_info=True,
            )

        finally:
            time.sleep(20)
            yield item
