"""Unit tests for the BooksTWSpider."""

import json
import os
import unittest
from unittest.mock import patch

from scrapy.http import HtmlResponse, Request

from comic_scrapers.items import OrphanVolumeItem
from comic_scrapers.spiders.books_tw import BooksTWSpider

FILE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestBooksTWSpiderParse(unittest.TestCase):
    """Test cases for the parse() method of BooksTWSpider."""

    def setUp(self):
        """Set up test fixtures."""
        self.spider = BooksTWSpider()

    def test_parse_extracts_book_urls_correctly(self):
        """Test that parse() correctly extracts book URLs from the page."""
        # Get sample forthcoming page HTML
        html_content = ""
        with open(
            f"{FILE_DIR}/test_books_tw_forthcoming_page.html", "r", encoding="utf-8"
        ) as f:
            html_content = f.read()

        # Get sample results for comparison
        sample_results = []
        with open(f"{FILE_DIR}/test_books_tw_result.json", "r", encoding="utf-8") as f:
            sample_results = json.load(f)

        # Create a mock response with sample HTML containing book links
        url = "https://www.books.com.tw/web/sys_compub/books/16/?loc=P_0001_017"
        request = Request(url=url)
        response = HtmlResponse(
            url=url,
            request=request,
            body=html_content.encode("utf-8"),
            encoding="utf-8",
        )

        # Call parse method
        results = list(self.spider.parse(response))

        # Verify results
        self.assertEqual(
            len(results),
            len(sample_results),
            f"Should extract exactly {len(sample_results)} book URLs",
        )
        for i, result in enumerate(results):
            self.assertIsInstance(result, Request, "Should yield Request objects")
            # Check that the URL matches the expected source_url from sample data
            self.assertIn(
                "books.com.tw/products/", result.url, "URL should be a product page"
            )

    def test_parse_handles_empty_page(self):
        """Test that parse() handles pages with no book links gracefully."""
        # Create a mock response with no book links
        html_content = """
        <html>
            <body>
                <div class="empty-results">
                    <p>No books found</p>
                </div>
            </body>
        </html>
        """
        url = "https://www.books.com.tw/web/sys_compub/books/16/?loc=P_0001_017"
        request = Request(url=url)
        response = HtmlResponse(
            url=url, request=request, body=html_content, encoding="utf-8"
        )

        # Call parse method
        results = list(self.spider.parse(response))

        # Verify results
        self.assertEqual(
            len(results), 0, "Should return empty list for pages with no books"
        )


class TestBooksTWSpiderParseVolumeInfo(unittest.TestCase):
    """Test cases for the parse_volume_info() method of BooksTWSpider."""

    def setUp(self):
        """Set up test fixtures."""
        self.spider = BooksTWSpider()

    @patch("time.sleep", return_value=None)
    def test_parse_volume_info_extracts_isbn_correctly(self, mock_sleep):
        """Test that parse_volume_info() correctly extracts ISBN from the page."""
        # Get sample response HTML with ISBN
        html_content = ""
        with open(
            f"{FILE_DIR}/test_books_tw_one_volume_page.html", "r", encoding="utf-8"
        ) as f:
            html_content = f.read()

        # Create a mock response with sample HTML containing ISBN
        url = "https://www.books.com.tw/products/0011035314?loc=P_0004_001"
        request = Request(url=url)
        response = HtmlResponse(
            url=url,
            request=request,
            body=html_content.encode("utf-8"),
            encoding="utf-8",
        )

        # Call parse_volume_info method
        results = list(self.spider.parse_volume_info(response))

        # Verify results
        self.assertEqual(len(results), 1, "Should yield exactly one item")
        item = results[0]
        self.assertIsInstance(item, OrphanVolumeItem, "Should yield OrphanVolumeItem")
        self.assertEqual(
            item["isbn_tw"], "9786260261665", "Should extract correct ISBN"
        )
        self.assertEqual(item["source_url"], url, "Should set correct source URL")
        mock_sleep.assert_called_once_with(20)

    @patch("time.sleep", return_value=None)
    def test_parse_volume_info_handles_missing_isbn(self, mock_sleep):
        """Test that parse_volume_info() handles pages without ISBN gracefully."""
        # Create a mock response without ISBN
        html_content = """
        <html>
            <body>
                <div class="bd">
                    <ul>
                        <li>作者：測試作者</li>
                        <li>出版社：測試出版社</li>
                    </ul>
                </div>
            </body>
        </html>
        """

        # Create a mock response with sample HTML missing ISBN
        url = "https://www.books.com.tw/products/0011036936?loc=P_0004_074"
        request = Request(url=url)
        response = HtmlResponse(
            url=url,
            request=request,
            body=html_content.encode("utf-8"),
            encoding="utf-8",
        )

        # Call parse_volume_info method
        results = list(self.spider.parse_volume_info(response))

        # Verify results
        self.assertEqual(len(results), 1, "Should still yield an item")
        item = results[0]
        self.assertIsInstance(item, OrphanVolumeItem, "Should yield OrphanVolumeItem")
        self.assertIsNone(item["isbn_tw"], "ISBN should be None when not found")
        self.assertEqual(item["source_url"], url, "Should set correct source URL")
        mock_sleep.assert_called_once_with(20)

    @patch("time.sleep", return_value=None)
    def test_parse_volume_info_epub_isbns_are_ignored(self, mock_sleep):
        """Test that parse_volume_info() correctly ignores EPUB ISBNs."""
        # Get sample response HTML with EISBN
        html_content = ""
        with open(
            f"{FILE_DIR}/test_books_tw_epub_page.html", "r", encoding="utf-8"
        ) as f:
            html_content = f.read()

        # Create a mock response with sample HTML containing EISBN
        url = "https://www.books.com.tw/products/E050293642"
        request = Request(url=url)
        response = HtmlResponse(
            url=url,
            request=request,
            body=html_content.encode("utf-8"),
            encoding="utf-8",
        )

        # Call parse_volume_info method
        results = list(self.spider.parse_volume_info(response))

        # Verify results
        self.assertEqual(len(results), 1, "Should yield exactly one item")
        item = results[0]
        self.assertNotIn(
            "isbn_tw", item, "Should not set isbn_tw field for EPUB volumes"
        )
        mock_sleep.assert_called_once_with(20)


if __name__ == "__main__":
    unittest.main()
