import scrapy
from scrapy.http import Request, Response

class BooksJpSpider(scrapy.Spider):
    name = "books_jp"

    def start_requests(self):
        """
        Obtain book links from the books.or.jp search results page
        """
        pass

    def parse_search_result(self, response: Response):
        """
        Obtain book links from the books.or.jp search results page
        """
        pass

    def parse_comic_info(self, response: Response):
        """
        Extract comic information from the book link
        Information includes title_jp, author_jp, status_jp
        """
        pass

    def parse_volume_info(self, response: Response):
        """
        Extract volume information from the book link
        Information includes volume_number, release_date_jp, isbn_jp, publisher_jp
        """
        pass
