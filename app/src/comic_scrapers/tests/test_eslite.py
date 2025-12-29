"""Unit and Integration tests for Eslite spiders.

Test Types:
-----------
- **Unit Tests**: Test individual methods/logic with all dependencies mocked.
  Focus on single responsibility and isolated behavior.

- **Integration Tests**: Test component collaboration and workflows.
  Mock external resources (Selenium, Django ORM) but test actual interaction flow.

- **E2E Tests**: Real website scraping tests are NOT included here.
  They should be in a separate integration test suite.

Test Execution:
---------------
- All tests use mocked HTTP responses and Selenium interactions
- No real network requests or database operations
- Fast execution suitable for CI/CD

Coverage:
---------
- Spider initialization and configuration
- Search results extraction workflow
- Detail page parsing logic
- Date filtering and topic matching
- Lifecycle management (driver cleanup)
"""

import unittest
from unittest.mock import MagicMock, patch

from scrapy.http import HtmlResponse, Request
from selenium.common.exceptions import (
    TimeoutException,
)

from comic_scrapers.items import OrphanMapItem
from comic_scrapers.spiders.eslite import (
    EsliteISBNSpider,
    EsliteSpider,
    EsliteTitleTwSpider,
)


class TestEsliteSpiderParse(unittest.TestCase):
    """[INTEGRATION] Test parse() method workflow.

    Tests the complete parse() flow including search value iteration
    and interaction with parse_search_results().
    """

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            self.spider = EsliteSpider(
                search_value="測試漫畫1", last_release_date="2025-12-15"
            )
            self.spider.search_field_name = "title_tw"

            # Mock driver and its methods
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.eslite.com"
            self.spider.driver.page_source = "<html><body>Test</body></html>"

    def test_parse_processes_single_search_value(self):
        """Test that parse() processes the configured search_value."""
        # Mock search box element
        mock_search_box = MagicMock()
        self.spider.driver.find_element.return_value = mock_search_box

        # Mock parse_search_results to return one item
        mock_parse = MagicMock(return_value=iter([OrphanMapItem()]))

        with (
            patch.object(self.spider, "parse_search_results", mock_parse),
            patch.object(self.spider, "perform_search"),
        ):
            url = "https://www.eslite.com"
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
                search_value="測試漫畫1", last_release_date="2025-12-15"
            )

    def test_parse_raises_error_without_search_value(self):
        """Test that parse() raises ValueError when search_value is None."""
        # Create spider without search_value
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            spider = EsliteSpider(search_value=None)
            spider.search_field_name = "title_tw"
            spider.driver = MagicMock()

            url = "https://www.eslite.com"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            with self.assertRaises(ValueError) as context:
                list(spider.parse(response))

            self.assertIn("search_value", str(context.exception))


class TestEsliteSpiderParseSearchResults(unittest.TestCase):
    """[INTEGRATION] Test parse_search_results() workflow.

    Tests URL extraction, date filtering logic, and interaction with
    parse_detail_info(). These are integration tests as they validate
    the collaboration between multiple components.
    """

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            self.spider = EsliteSpider(search_value="測試漫畫", last_release_date=None)
            self.spider.search_field_name = "title_tw"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.eslite.com/search"
            self.spider.wait = MagicMock()

    def test_parse_search_results_extracts_urls(self):
        """Test that parse_search_results() extracts book URLs correctly."""
        num_urls = 3

        # Mock category element for apply_search_filters
        mock_category = MagicMock()

        # Create mock URL and date elements
        mock_urls = [MagicMock() for _ in range(num_urls)]
        mock_dates = []
        for i, day in enumerate([18, 17, 16], 1):
            mock_date = MagicMock()
            # base_selenium_spider calls get_attribute("innerHTML")
            mock_date.get_attribute.return_value = f"2025年12月{day}日"
            mock_dates.append(mock_date)

        # Configure wait.until calls
        # Order: apply_search_filters (2 calls) → URLs → dates
        # → URL refresh (3x) → next button
        self.spider.wait.until.side_effect = [
            mock_category,  # 1. Category filter click (apply_search_filters)
            True,  # 2. Staleness check (apply_search_filters)
            mock_urls,  # 3. Initial URL elements
            mock_dates,  # 4. Date elements
            *([mock_urls] * num_urls),  # 5-7. URL refresh after each detail page
            TimeoutException("No next button"),  # 8. No next page
        ]

        # Mock parse_detail_info to yield an item for each call
        # Note: Must use lambda to create a new iterator for each call
        with patch.object(
            self.spider,
            "parse_detail_info",
            side_effect=lambda *args, **kwargs: iter([OrphanMapItem()]),
        ):
            results = list(
                self.spider.parse_search_results(
                    search_value="測試漫畫", last_release_date=None
                )
            )

            # Should process all URLs
            self.assertEqual(
                len(results), num_urls, f"Should process all {num_urls} URLs"
            )

    def test_parse_search_results_skips_old_releases(self):
        """Test that parse_search_results() skips books with old release dates."""
        # Mock category element for apply_search_filters
        mock_category = MagicMock()

        # Create mock URL and date elements
        num_urls = 2
        mock_urls = [MagicMock() for _ in range(num_urls)]
        mock_dates = []
        for day in [15, 16]:  # Both older than 2025-12-18
            mock_date = MagicMock()
            mock_date.get_attribute.return_value = f"2025年12月{day}日"
            mock_dates.append(mock_date)

        # Order: apply_search_filters (2 calls) → URLs → dates → next button
        self.spider.wait.until.side_effect = [
            mock_category,  # 1. Category filter click
            True,  # 2. Staleness check
            mock_urls,  # 3. URLs
            mock_dates,  # 4. Dates (all old)
            TimeoutException("No next button"),  # 5. No next page (all skipped)
        ]

        results = list(
            self.spider.parse_search_results(
                search_value="測試漫畫",
                last_release_date="2025-12-18",  # All dates are older
            )
        )

        # Should skip all URLs due to old dates, and stop when no next button found
        self.assertEqual(len(results), 0, "Should skip all URLs with old release dates")


class TestEsliteSpiderParseDetailInfo(unittest.TestCase):
    """[INTEGRATION] Test parse_detail_info() extraction workflow.

    Tests complete detail page parsing including navigation, field extraction,
    and validation. Focuses on Eslite-specific extraction logic.
    """

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.base_selenium_spider.webdriver"):
            self.spider = EsliteSpider(search_value="測試漫畫")
            self.spider.search_field_name = "title_tw"
            self.spider.verify_element_xpath = "//h1[@class='test']"

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

        # Mock find_element for book details using data-driven approach
        field_mapping = {
            "h4": "テスト漫画",  # title_jp
            "h1": "測試漫畫",  # title_tw
            "author": "作\n者：\n測試作者",  # author_tw
            "publicDate": "出\n版\n日\n期：\n2025/11/18",  # release_date_tw
            "publisher": "出\n版\n社：\n測試出版社",  # publisher_tw
        }

        def mock_find_element(by, xpath):
            mock_elem = MagicMock()
            for key, value in field_mapping.items():
                if key in xpath:
                    mock_elem.text = value
                    break
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


class TestEsliteISBNSpiderIntegration(unittest.TestCase):
    """[INTEGRATION] Test EsliteISBNSpider initialization and configuration.

    Tests spider initialization with Django ORM integration (mocked)
    and proper configuration of search parameters.
    """

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_eslite_isbn_spider_initialization(self, mock_webdriver):
        """Test EsliteISBNSpider initialization with search_value."""
        spider = EsliteISBNSpider(search_value="9789861234567")

        # Verify basic initialization
        self.assertEqual(spider.name, "eslite_isbn")
        self.assertEqual(spider.search_field_name, "isbn_tw")
        self.assertEqual(spider.search_value, "9789861234567")

        # Verify XPath configuration
        self.assertEqual(
            spider.verify_element_xpath,
            "//div[@class='product-description-schema']",
            "Should use product-description-schema for ISBN searches",
        )

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_eslite_isbn_spider_requires_search_value(self, mock_webdriver):
        """Test EsliteISBNSpider raises ValueError without search_value."""
        with self.assertRaises(ValueError) as context:
            EsliteISBNSpider(search_value=None)

        self.assertIn("ISBN", str(context.exception))
        self.assertIn("required", str(context.exception))


class TestEsliteTitleTwSpiderIntegration(unittest.TestCase):
    """[UNIT + INTEGRATION] Test EsliteTitleTwSpider configuration.

    Includes both unit tests (custom parameter handling) and integration tests
    (initialization with Django ORM).
    """

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_eslite_title_tw_spider_initialization(self, mock_webdriver):
        """Test EsliteTitleTwSpider initialization with search_value."""
        spider = EsliteTitleTwSpider(
            search_value="測試漫畫1", last_release_date="2025-12-18"
        )

        # Verify basic initialization
        self.assertEqual(spider.name, "eslite_title_tw")
        self.assertEqual(spider.search_field_name, "title_tw")
        self.assertEqual(spider.search_value, "測試漫畫1")
        self.assertEqual(spider.last_release_date, "2025-12-18")

        # Verify XPath configuration
        self.assertEqual(
            spider.verify_element_xpath,
            "//h1[@class='sans-font-semi-bold']",
            "Should use h1 title for title_tw searches",
        )

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_eslite_title_tw_spider_requires_search_value(self, mock_webdriver):
        """Test EsliteTitleTwSpider raises ValueError without search_value."""
        with self.assertRaises(ValueError) as context:
            EsliteTitleTwSpider(search_value=None, last_release_date="2025-12-01")

        self.assertIn("title_tw", str(context.exception))
        self.assertIn("required", str(context.exception))


if __name__ == "__main__":
    unittest.main()
