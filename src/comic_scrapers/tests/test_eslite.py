"""Unit and Integration tests for the Eslite spiders."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from scrapy.http import HtmlResponse, Request
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from comic_scrapers.items import OrphanMapItem
from comic_scrapers.spiders.eslite import (
    EsliteISBNSpider,
    EsliteSpider,
    EsliteTitleTwSpider,
)


class TestEsliteSpiderGetBookReleaseDate(unittest.TestCase):
    """Test cases for the _get_book_release_date() method of EsliteSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.eslite.webdriver"):
            self.spider = EsliteSpider()

    def test_get_book_release_date_valid_format(self):
        """Test that _get_book_release_date() correctly parses valid date."""
        product_desc = "出版日期：2025年12月18日\n"
        result = self.spider._get_book_release_date(product_desc)
        self.assertEqual(result, "2025-12-18", "Should parse date correctly")

    def test_get_book_release_date_single_digit_month_day(self):
        """Test that _get_book_release_date() pads single digit months/days."""
        product_desc = "出版日期：2018年1月6日\n"
        result = self.spider._get_book_release_date(product_desc)
        self.assertEqual(
            result, "2018-01-06", "Should pad month and day with leading zeros"
        )

    def test_get_book_release_date_invalid_format(self):
        """Test that _get_book_release_date() returns None for invalid format."""
        product_desc = "Some random text without date"
        result = self.spider._get_book_release_date(product_desc)
        self.assertIsNone(result, "Should return None for invalid date format")


class TestEsliteSpiderParse(unittest.TestCase):
    """Test cases for the parse() method of EsliteSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.eslite.webdriver"):
            self.spider = EsliteSpider()
            self.spider.topic = "title_tw"
            self.spider.topic_list = ["測試漫畫1", "測試漫畫2", "測試漫畫3"]

            # Mock driver and its methods
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.eslite.com"
            self.spider.driver.page_source = "<html><body>Test</body></html>"

    def test_parse_processes_topic_list(self):
        """Test that parse() processes items from topic_list."""
        # Mock search box element
        mock_search_box = MagicMock()
        self.spider.driver.find_element.return_value = mock_search_box
        print(f"Mock search box: {mock_search_box}")

        # Mock parse_search_results to avoid actual processing
        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.eslite.com"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            results = list(self.spider.parse(response))

            # Should process 3 items
            self.assertEqual(
                len(results),
                3,
                "Should process all items in topic_list",
            )

    def test_parse_handles_timeout_exception(self):
        """Test that parse() handles TimeoutException gracefully."""
        # Make find_element raise TimeoutException
        self.spider.driver.find_element.side_effect = TimeoutException("Timeout")

        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.eslite.com"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            # Should not raise exception
            results = list(self.spider.parse(response))
            # Should still complete without crashing
            self.assertIsInstance(results, list)

    def test_parse_handles_no_such_element_exception(self):
        """Test that parse() handles NoSuchElementException gracefully."""
        # Make find_element raise NoSuchElementException
        self.spider.driver.find_element.side_effect = NoSuchElementException(
            "Not found"
        )

        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.eslite.com"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            # Should not raise exception
            results = list(self.spider.parse(response))
            # Should still complete without crashing
            self.assertIsInstance(results, list)


class TestEsliteSpiderParseSearchResults(unittest.TestCase):
    """Test cases for the parse_search_results() method of EsliteSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.eslite.webdriver"):
            self.spider = EsliteSpider()
            self.spider.topic = "title_tw"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.eslite.com/search"
            self.spider.wait = MagicMock()

    def test_parse_search_results_extracts_urls(self):
        """Test that parse_search_results() extracts book URLs correctly."""
        # Mock category element
        mock_category = MagicMock()

        # Mock URL elements
        mock_url1 = MagicMock()
        mock_url2 = MagicMock()
        mock_url3 = MagicMock()

        # Mock release date elements
        mock_date1 = MagicMock()
        mock_date1.get_attribute.return_value = "2025年12月18日"
        mock_date2 = MagicMock()
        mock_date2.get_attribute.return_value = "2025年12月17日"
        mock_date3 = MagicMock()
        mock_date3.get_attribute.return_value = "2025年12月16日"

        # Configure wait to return mocked elements
        self.spider.wait.until.side_effect = [
            mock_category,  # First call: category filter (for prev_url is None)
            [mock_url1, mock_url2, mock_url3],  # Second call: URLs
            [mock_date1, mock_date2, mock_date3],  # Third call: dates
            [mock_url1, mock_url2, mock_url3],  # After processing URL 1: refresh
            [mock_url1, mock_url2, mock_url3],  # After processing URL 2: refresh
            [mock_url1, mock_url2, mock_url3],  # After processing URL 3: refresh
            TimeoutException("No next button"),  # Next page button not found
        ]

        # Mock parse_detail_info to return a new iterator each time it's called
        def mock_parse_detail_info(*args, **kwargs):
            return iter([OrphanMapItem()])

        with patch.object(
            self.spider, "parse_detail_info", side_effect=mock_parse_detail_info
        ):
            results = list(self.spider.parse_search_results("測試漫畫", 0, None))

            # Should process all 3 URLs
            self.assertEqual(len(results), 3, "Should process all 3 URLs")

    def test_parse_search_results_handles_timeout(self):
        """Test that parse_search_results() handles timeout when no URLs found."""
        # Make wait.until raise TimeoutException on category filter click
        self.spider.wait.until.side_effect = TimeoutException("No elements found")

        results = list(self.spider.parse_search_results("測試漫畫", 0, None))

        # Should yield one empty item with search_url
        self.assertEqual(len(results), 1, "Should yield one item on timeout")
        self.assertIn("search_url", results[0])

    def test_parse_search_results_skips_old_releases(self):
        """Test that parse_search_results() skips books with old release dates."""
        self.spider.last_release_dates = ["2025-12-18"]

        # Mock category element
        mock_category = MagicMock()

        # Mock URL elements
        mock_url1 = MagicMock()
        mock_url2 = MagicMock()

        # Mock release date elements - both older than last_release_dates
        mock_date1 = MagicMock()
        mock_date1.get_attribute.return_value = "2025年12月15日"
        mock_date2 = MagicMock()
        mock_date2.get_attribute.return_value = "2025年12月16日"

        self.spider.wait.until.side_effect = [
            mock_category,  # First call: category filter (for prev_url is None)
            [mock_url1, mock_url2],  # Second call: URLs
            [mock_date1, mock_date2],  # Third call: dates
            TimeoutException(
                "No next button"
            ),  # Next page button not found (since all URLs skipped)
        ]

        results = list(self.spider.parse_search_results("測試漫畫", 0, None))

        # Should skip all URLs due to old dates
        self.assertEqual(len(results), 0, "Should skip all URLs with old release dates")


class TestEsliteSpiderParseDetailInfo(unittest.TestCase):
    """Test cases for the parse_detail_info() method of EsliteSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.eslite.webdriver"):
            self.spider = EsliteSpider()
            self.spider.topic = "title_tw"
            self.spider.target_info = "//h1[@class='test']"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.eslite.com/product/123"
            self.spider.wait = MagicMock()

    def test_parse_detail_info_extracts_all_fields(self):
        """Test that parse_detail_info() extracts all book information correctly."""
        # Create item
        item = OrphanMapItem()
        item["title_tw"] = "測試漫畫"

        # Mock URL element
        mock_url = MagicMock()

        # Mock target info element
        mock_target = MagicMock()
        mock_target.get_attribute.return_value = "測試漫畫 by 作者"

        # Mock product description element
        mock_desc = MagicMock()
        mock_desc.get_attribute.return_value = "ISBN: 9789861234567"

        # Configure wait.until
        self.spider.wait.until.side_effect = [
            mock_target,  # topic_prevent
            mock_target,  # category check
            mock_desc,  # product_desc
        ]

        # Mock find_element for book details
        def mock_find_element(by, xpath):
            mock_elem = MagicMock()
            if "h4" in xpath:  # title_jp
                mock_elem.text = "テスト漫画"
            elif "h1" in xpath:  # title_tw
                mock_elem.text = "測試漫畫"
            elif "author" in xpath:  # author_tw
                mock_elem.text = "作\n者：\n測試作者"
            elif "publicDate" in xpath:  # release_date_tw
                mock_elem.text = "出\n版\n日\n期：\n2025/11/18"
            elif "publisher" in xpath:  # publisher_tw
                mock_elem.text = "出\n版\n社：\n測試出版社"
            return mock_elem

        self.spider.driver.find_element.side_effect = mock_find_element

        results = list(self.spider.parse_detail_info(mock_url, item))

        # Should yield one item with all fields populated
        self.assertEqual(len(results), 1, "Should yield one item")
        result_item = results[0]
        self.assertEqual(result_item["title_jp"], "テスト漫画")
        self.assertEqual(result_item["title_tw"], "測試漫畫")
        self.assertEqual(result_item["author_tw"], "作\n者：\n測試作者")
        self.assertEqual(result_item["release_date_tw"], "出\n版\n日\n期：\n2025/11/18")
        self.assertEqual(result_item["publisher_tw"], "出\n版\n社：\n測試出版社")

    def test_parse_detail_info_handles_topic_mismatch(self):
        """Test that parse_detail_info() returns early on topic mismatch."""
        # Create item
        item = OrphanMapItem()
        item["title_tw"] = "測試漫畫"

        # Mock URL element
        mock_url = MagicMock()

        # Mock target info element - doesn't contain topic
        mock_target = MagicMock()
        mock_target.get_attribute.return_value = "不同的標題"

        # Mock product description element
        mock_desc = MagicMock()
        mock_desc.get_attribute.return_value = "ISBN: 9789861234567"

        self.spider.wait.until.side_effect = [
            mock_target,  # topic_prevent
            mock_target,  # category check
            mock_desc,  # product_desc
        ]

        results = list(self.spider.parse_detail_info(mock_url, item))

        # Should yield item early without processing
        self.assertEqual(len(results), 1, "Should yield one item")
        # Should have called driver.back()
        self.spider.driver.back.assert_called()

    def test_parse_detail_info_handles_timeout(self):
        """Test that parse_detail_info() handles TimeoutException gracefully."""
        # Create item
        item = OrphanMapItem()
        item["title_tw"] = "測試漫畫"

        # Mock URL element
        mock_url = MagicMock()

        # Make wait.until raise TimeoutException
        self.spider.wait.until.side_effect = TimeoutException("Element not found")

        results = list(self.spider.parse_detail_info(mock_url, item))

        # Should handle exception and navigate back
        self.spider.driver.back.assert_called()
        # Should not yield item on timeout
        self.assertEqual(len(results), 0, "Should not yield item on timeout")


class TestEsliteISBNSpiderIntegration(unittest.TestCase):
    """Integration tests for EsliteISBNSpider."""

    @patch("comic_scrapers.spiders.eslite.Volume")
    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_eslite_isbn_spider_initialization(self, mock_webdriver, mock_volume):
        """Test that EsliteISBNSpider initializes with correct topic and topic_list."""
        # Mock Volume.objects query
        mock_volume.objects.filter.return_value.values_list.return_value = [
            "9789861234567",
            "9789861234568",
            "9789861234569",
        ]

        spider = EsliteISBNSpider()

        self.assertEqual(spider.name, "eslite_isbn")
        self.assertEqual(spider.topic, "isbn_tw")
        self.assertEqual(len(spider.topic_list), 3)
        self.assertIn("9789861234567", spider.topic_list)

    @patch("comic_scrapers.spiders.eslite.Volume")
    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_eslite_isbn_spider_target_info_xpath(self, mock_webdriver, mock_volume):
        """Test that EsliteISBNSpider sets correct target_info xpath."""
        mock_volume.objects.filter.return_value.values_list.return_value = []

        spider = EsliteISBNSpider()

        self.assertEqual(
            spider.target_info,
            "//div[@class='product-description-schema']",
            "Should use product-description-schema for ISBN searches",
        )

    @patch("comic_scrapers.spiders.eslite.Volume")
    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_eslite_isbn_spider_empty_volume_list(self, mock_webdriver, mock_volume):
        """Test that EsliteISBNSpider handles empty volume list."""
        mock_volume.objects.filter.return_value.values_list.return_value = []

        spider = EsliteISBNSpider()

        self.assertEqual(len(spider.topic_list), 0)


class TestEsliteTitleTwSpiderIntegration(unittest.TestCase):
    """Integration tests for EsliteTitleTwSpider."""

    @patch("comic_scrapers.spiders.eslite.Series")
    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_eslite_title_tw_spider_initialization(self, mock_webdriver, mock_series):
        """Test that EsliteTitleTwSpider initializes with correct topic & topic_list."""
        # Mock Series.objects query
        mock_series.objects.filter.return_value.values_list.side_effect = [
            ["測試漫畫1", "測試漫畫2"],  # title_tw
            [datetime(2025, 12, 18), datetime(2025, 12, 17)],  # last_release_date
        ]

        spider = EsliteTitleTwSpider()

        self.assertEqual(spider.name, "eslite_title_tw")
        self.assertEqual(spider.topic, "title_tw")
        self.assertEqual(len(spider.topic_list), 2)
        self.assertEqual(len(spider.last_release_dates), 2)
        self.assertIn("測試漫畫1", spider.topic_list)

    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_eslite_title_tw_spider_custom_topic_list(self, mock_webdriver):
        """Test that EsliteTitleTwSpider accepts custom topic_list."""
        custom_list = ["自訂漫畫1", "自訂漫畫2"]
        custom_dates = ["2025-01-01", "2025-02-01"]

        spider = EsliteTitleTwSpider(
            topic_list=custom_list, last_release_dates=custom_dates
        )

        self.assertEqual(spider.topic_list, custom_list)
        self.assertEqual(spider.last_release_dates, custom_dates)

    @patch("comic_scrapers.spiders.eslite.Series")
    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_eslite_title_tw_spider_target_info_xpath(
        self, mock_webdriver, mock_series
    ):
        """Test that EsliteTitleTwSpider sets correct target_info xpath."""
        mock_series.objects.filter.return_value.values_list.side_effect = [[], []]

        spider = EsliteTitleTwSpider()

        self.assertEqual(
            spider.target_info,
            "//h1[@class='sans-font-semi-bold']",
            "Should use h1 title for title_tw searches",
        )


class TestEsliteSpiderClosed(unittest.TestCase):
    """Test cases for the closed() method of EsliteSpider."""

    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_closed_quits_driver(self, mock_webdriver):
        """Test that closed() method quits the Selenium driver."""
        spider = EsliteSpider()
        mock_driver = MagicMock()
        spider.driver = mock_driver

        spider.closed("finished")

        mock_driver.quit.assert_called_once()

    @patch("comic_scrapers.spiders.eslite.webdriver")
    def test_closed_handles_none_driver(self, mock_webdriver):
        """Test that closed() handles None driver gracefully."""
        spider = EsliteSpider()
        spider.driver = None

        # Should not raise exception
        spider.closed("finished")

    # @patch("comic_scrapers.spiders.eslite.webdriver")
    # def test_closed_handles_driver_quit_exception(self, mock_webdriver):
    #     """Test that closed() handles exception during driver.quit()."""
    #     spider = EsliteSpider()
    #     mock_driver = MagicMock()
    #     mock_driver.quit.side_effect = Exception("Quit failed")
    #     spider.driver = mock_driver

    #     # Should not raise exception
    #     try:
    #         spider.closed("finished")
    #     except Exception:
    #         self.fail("closed() should handle driver.quit() exceptions")


if __name__ == "__main__":
    unittest.main()
