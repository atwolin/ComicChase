"""Unit and Integration tests for the BooksJp spiders."""

import unittest
from unittest.mock import MagicMock, patch

from scrapy.http import HtmlResponse, Request
from selenium.common.exceptions import (
    TimeoutException,
)

from comic_scrapers.items import JpComicItem
from comic_scrapers.spiders.books_jp import BooksJpSpider, BooksJpTitleTwSpider


class TestBooksJpSpiderParse(unittest.TestCase):
    """Test cases for the parse() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            self.spider = BooksJpSpider(
                search_value="廊天のアルバス", last_release_date="2025-12-15"
            )
            self.spider.search_field_name = "title_jp"
            self.spider.title_jp = "廊天のアルバス"

            # Mock driver and its methods
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/"
            self.spider.driver.page_source = "<html><body>Test</body></html>"

    def test_parse_processes_single_search_value(self):
        """Test that parse() processes the configured search_value."""
        # Mock search box and button elements
        mock_search_box = MagicMock()
        mock_search_button = MagicMock()

        def mock_find_element(by, xpath):
            if "searchforbooks_title" in xpath:
                return mock_search_box
            elif "searchforbooks_search_button" in xpath:
                return mock_search_button
            return MagicMock()

        self.spider.driver.find_element.side_effect = mock_find_element

        # Mock parse_search_results to return one item
        mock_parse = MagicMock(return_value=iter([JpComicItem()]))

        with patch.object(
            self.spider, "parse_search_results", mock_parse
        ), patch.object(self.spider, "perform_search"):
            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            results = list(self.spider.parse(response))

            # Should process single search_value and yield 1 result
            self.assertEqual(
                len(results),
                1,
                "Should process the configured search_value",
            )
            # Verify parse_search_results was called once with correct parameters
            mock_parse.assert_called_once_with(
                search_value="廊天のアルバス", last_release_date="2025-12-15"
            )

    def test_parse_raises_error_without_search_value(self):
        """Test that parse() raises ValueError when search_value is None."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            spider = BooksJpSpider(search_value=None)
            spider.search_field_name = "title_jp"
            spider.driver = MagicMock()

            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            with self.assertRaises(ValueError) as context:
                list(spider.parse(response))

            self.assertIn("search_value", str(context.exception))


class TestBooksJpSpiderParseSearchResults(unittest.TestCase):
    """Test cases for the parse_search_results() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            self.spider = BooksJpSpider(
                search_value="廊天のアルバス", last_release_date=None
            )
            self.spider.search_field_name = "title_jp"
            self.spider.title_jp = "廊天のアルバス"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/search"
            self.spider.wait = MagicMock()

    def test_parse_search_results_extracts_links(self):
        """Test that parse_search_results() extracts book links correctly."""
        num_links = 3

        # Create mock link and date elements
        mock_links = [MagicMock() for _ in range(num_links)]
        mock_dates = []
        for day in [18, 17, 16]:
            mock_date = MagicMock()
            mock_date.get_attribute.return_value = f"発売日：2025年12月{day}日"
            mock_dates.append(mock_date)

        # Configure wait.until calls
        self.spider.wait.until.side_effect = [
            mock_links,  # Initial link elements
            mock_dates,  # Date elements
            *([mock_links] * num_links),  # Link refresh after each detail page
            TimeoutException("No next page"),  # No next page
        ]

        # Mock parse_detail_info to yield an item for each call
        # Note: Must use lambda to create a new iterator for each call
        with patch.object(
            self.spider,
            "parse_detail_info",
            side_effect=lambda *args, **kwargs: iter([JpComicItem()]),
        ):
            results = list(
                self.spider.parse_search_results(
                    search_value="廊天のアルバス", last_release_date=None
                )
            )

            # Should process all links
            self.assertEqual(
                len(results), num_links, f"Should process all {num_links} links"
            )

    def test_parse_search_results_skips_old_releases(self):
        """Test that parse_search_results() skips books with old release dates."""
        # Create mock link and date elements
        num_links = 2
        mock_links = [MagicMock() for _ in range(num_links)]
        mock_dates = []
        for day in [15, 16]:  # Both older than 2025-12-18
            mock_date = MagicMock()
            mock_date.get_attribute.return_value = f"発売日：2025年12月{day}日"
            mock_dates.append(mock_date)

        self.spider.wait.until.side_effect = [
            mock_links,  # Links
            mock_dates,  # Dates (all old)
            TimeoutException("No next page"),  # No next page (all skipped)
        ]

        results = list(
            self.spider.parse_search_results(
                search_value="廊天のアルバス",
                last_release_date="2025-12-18",  # All dates are older
            )
        )

        # Should skip all links due to old dates
        self.assertEqual(
            len(results), 0, "Should skip all links with old release dates"
        )


class TestBooksJpSpiderParseDetailInfo(unittest.TestCase):
    """Test cases for the parse_detail_info() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            self.spider = BooksJpSpider(search_value="廊天のアルバス")
            self.spider.search_field_name = "title_jp"
            self.spider.verify_element_xpath = "//span[@class='bookdetail_title_text']"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/book/123"
            self.spider.wait = MagicMock()

    def test_parse_detail_info_extracts_all_fields(self):
        """Test that parse_detail_info() extracts all book information correctly."""
        self.spider.title_jp = "廻天のアルバス"
        # Create item
        item = JpComicItem()
        item["search_query"] = self.spider.title_jp

        # Mock link element
        mock_link = MagicMock()

        # Mock target info element
        mock_target = MagicMock()
        mock_target.get_attribute.return_value = "廻天のアルバス ７"

        # Mock product description element - matches real format from jp_titletw.json
        mock_desc = MagicMock()
        mock_desc.get_attribute.return_value = (
            '<p class="text-body text-color">ISBN：9784098543724<br>'
            "雑誌コード：5854372<br>出版社：小学館<br>判型：新書<br>"
            "ページ数：192ページ<br>定価：540円（本体）<br>"
            "発行年月日：2025年12月23日<br>発売予定日：2025年12月18日"
            '<span class="readonly">。</span></p>'
        )

        # Configure wait.until
        self.spider.wait.until.side_effect = [
            mock_target,  # topic_prevent
            mock_desc,  # product_desc
        ]

        # Mock find_element and find_elements for book details
        def mock_find_element(by, xpath):
            mock_elem = MagicMock()
            if "bookdetail_title_text" in xpath:  # title_jp
                mock_elem.text = "廻天のアルバス ７"
            elif "bookdetail_publisher" in xpath:  # publisher_jp
                mock_elem.text = "出版社：小学館"
            return mock_elem

        def mock_find_elements(by, xpath):
            # Create author elements with different attributes
            author_texts = [
                "",
                "少年サンデーコミックス",
                "原案：牧 彰久",
                "絵：箭坪 幹",
            ]
            return [
                MagicMock(get_attribute=MagicMock(return_value=text))
                for text in author_texts
            ]

        self.spider.driver.find_element.side_effect = mock_find_element
        self.spider.driver.find_elements.side_effect = mock_find_elements

        results = list(self.spider.parse_detail_info(mock_link, item))

        # Should yield one item with all fields populated
        self.assertEqual(len(results), 1, "Should yield one item")
        result_item = results[0]
        self.assertEqual(result_item["title_jp"], "廻天のアルバス ７")
        self.assertEqual(result_item["publisher_jp"], "出版社：小学館")
        self.assertIsInstance(result_item["author_jp"], list)
        self.assertEqual(len(result_item["author_jp"]), 4)

    def test_parse_detail_info_handles_topic_mismatch(self):
        """Test that parse_detail_info() returns early on topic mismatch."""
        self.spider.title_jp = "廻天のアルバス"
        # Create item
        item = JpComicItem()
        item["search_query"] = self.spider.title_jp

        # Mock link element
        mock_link = MagicMock()

        # Mock target info element - doesn't contain topic
        mock_target = MagicMock()
        mock_target.get_attribute.return_value = "別の漫画"

        # Mock product description element
        mock_desc = MagicMock()
        mock_desc.get_attribute.return_value = "ISBN: 978-4-06-123456-7"

        self.spider.wait.until.side_effect = [
            mock_target,  # topic_prevent
            mock_desc,  # product_desc
        ]

        results = list(self.spider.parse_detail_info(mock_link, item))

        # Should yield item early without processing
        self.assertEqual(len(results), 1, "Should yield one item")
        # Should have called driver.back()
        self.spider.driver.back.assert_called()

    def test_parse_detail_info_handles_ebook(self):
        """Test that parse_detail_info() skips e-books."""
        self.spider.title_jp = "廻天のアルバス"
        # Create item
        item = JpComicItem()
        item["search_query"] = self.spider.title_jp

        # Mock link element
        mock_link = MagicMock()

        # Mock target info element
        mock_target = MagicMock()
        mock_target.get_attribute.return_value = "廻天のアルバス ７"

        # Mock product description element - contains e-book code
        mock_desc = MagicMock()
        mock_desc.get_attribute.return_value = "JP-eコード：123456"

        self.spider.wait.until.side_effect = [
            mock_target,  # topic_prevent
            mock_desc,  # product_desc
        ]

        results = list(self.spider.parse_detail_info(mock_link, item))

        # Should yield item early (e-book detected)
        self.assertEqual(len(results), 1, "Should yield one item")
        # Should have called driver.back()
        self.spider.driver.back.assert_called()


class TestBooksJpTitleTwSpiderIntegration(unittest.TestCase):
    """Integration tests for BooksJpTitleTwSpider."""

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_books_jp_title_spider_initialization(self, mock_webdriver):
        """Test BooksJpTitleTwSpider initialization with search_value."""
        spider = BooksJpTitleTwSpider(
            search_value="廊天のアルバス", last_release_date="2025-12-18"
        )

        # Verify basic initialization
        self.assertEqual(spider.name, "booksjp_title")
        self.assertEqual(spider.search_field_name, "title_jp")
        self.assertEqual(spider.search_value, "廊天のアルバス")
        self.assertEqual(spider.last_release_date, "2025-12-18")

        # Verify XPath configuration
        self.assertEqual(
            spider.verify_element_xpath,
            "//span[@class='bookdetail_title_text']",
            "Should use bookdetail_title_text for series name searches",
        )

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_books_jp_title_spider_requires_search_value(self, mock_webdriver):
        """Test BooksJpTitleTwSpider raises ValueError without search_value."""
        with self.assertRaises(ValueError) as context:
            BooksJpTitleTwSpider(search_value=None, last_release_date="2025-12-01")

        self.assertIn("title_jp", str(context.exception))
        self.assertIn("required", str(context.exception))


if __name__ == "__main__":
    unittest.main()
