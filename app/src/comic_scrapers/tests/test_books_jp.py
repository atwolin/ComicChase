"""Unit and Integration tests for the BooksJp spiders."""

import unittest
from unittest.mock import MagicMock, patch

from scrapy.http import HtmlResponse, Request
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from comic_scrapers.items import JpComicItem
from comic_scrapers.spiders.books_jp import BooksJpSpider, BooksJpTitleTwSpider


class TestBooksJpSpiderGetBookReleaseDate(unittest.TestCase):
    """Test cases for the _get_book_release_date() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.books_jp.webdriver"):
            self.spider = BooksJpSpider()

    def test_get_book_release_date_valid_format(self):
        """Test that _get_book_release_date() correctly parses valid date."""
        product_desc = "発売日：2025年12月18日\n"
        result = self.spider._get_book_release_date(product_desc)
        self.assertEqual(result, "2025-12-18", "Should parse date correctly")

    def test_get_book_release_date_single_digit_month_day(self):
        """Test that _get_book_release_date() pads single digit months/days."""
        product_desc = "発売予定日：2018年1月6日\n"
        result = self.spider._get_book_release_date(product_desc)
        self.assertEqual(
            result, "2018-01-06", "Should pad month and day with leading zeros"
        )

    def test_get_book_release_date_invalid_format(self):
        """Test that _get_book_release_date() returns None for invalid format."""
        product_desc = "Some random text without date"
        result = self.spider._get_book_release_date(product_desc)
        self.assertIsNone(result, "Should return None for invalid date format")


class TestBooksJpSpiderParse(unittest.TestCase):
    """Test cases for the parse() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.books_jp.webdriver"):
            self.spider = BooksJpSpider()
            self.spider.topic = "series_name"
            self.spider.topic_list = ["廻天のアルバス", "ブルーピリオド", "テスト漫画"]

            # Mock driver and its methods
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/"
            self.spider.driver.page_source = "<html><body>Test</body></html>"

    def test_parse_processes_topic_list(self):
        """Test that parse() processes items from topic_list."""
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

        # Mock parse_search_results to return one item per call
        mock_parse = MagicMock()
        mock_parse.side_effect = [
            iter([JpComicItem()]),  # First topic
            iter([JpComicItem()]),  # Second topic
            iter([JpComicItem()]),  # Third topic
        ]

        with patch.object(self.spider, "parse_search_results", mock_parse):
            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            results = list(self.spider.parse(response))

            # Should process all 3 items and yield 3 results
            self.assertEqual(
                len(results),
                3,
                "Should process all 3 items from topic_list",
            )
            # Verify parse_search_results was called 3 times
            self.assertEqual(mock_parse.call_count, 3)

    def test_parse_handles_timeout_exception(self):
        """Test that parse() handles TimeoutException gracefully."""
        # Make find_element raise TimeoutException
        self.spider.driver.find_element.side_effect = TimeoutException("Timeout")

        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.books.or.jp/"
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
            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            # Should not raise exception
            results = list(self.spider.parse(response))
            # Should still complete without crashing
            self.assertIsInstance(results, list)


class TestBooksJpSpiderParseSearchResults(unittest.TestCase):
    """Test cases for the parse_search_results() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.books_jp.webdriver"):
            self.spider = BooksJpSpider()
            self.spider.topic = "series_name"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/search"
            self.spider.wait = MagicMock()

    def test_parse_search_results_extracts_links(self):
        """Test that parse_search_results() extracts book links correctly."""
        # Mock link elements
        mock_link1 = MagicMock()
        mock_link2 = MagicMock()
        mock_link3 = MagicMock()

        # Mock release date elements
        mock_date1 = MagicMock()
        mock_date1.get_attribute.return_value = "発売日：2025年12月18日"
        mock_date2 = MagicMock()
        mock_date2.get_attribute.return_value = "発売日：2025年12月17日"
        mock_date3 = MagicMock()
        mock_date3.get_attribute.return_value = "発売日：2025年12月16日"

        # Configure wait to return mocked elements
        self.spider.wait.until.side_effect = [
            [mock_link1, mock_link2, mock_link3],  # First call: links
            [mock_date1, mock_date2, mock_date3],  # Second call: dates
            [mock_link1, mock_link2, mock_link3],  # After processing link 1: refresh
            [mock_link1, mock_link2, mock_link3],  # After processing link 2: refresh
            [mock_link1, mock_link2, mock_link3],  # After processing link 3: refresh
            TimeoutException("No next page"),  # Next page button not found
        ]

        # Mock parse_detail_info to return a new iterator each time it's called
        def mock_parse_detail_info(*args, **kwargs):
            return iter([JpComicItem()])

        with patch.object(
            self.spider, "parse_detail_info", side_effect=mock_parse_detail_info
        ):
            results = list(
                self.spider.parse_search_results("廻天のアルバス", series_index=0)
            )

            # Should process all 3 links
            self.assertEqual(len(results), 3, "Should process all 3 links")

    def test_parse_search_results_handles_timeout(self):
        """Test that parse_search_results() handles timeout when no links found."""
        # Make wait.until raise TimeoutException
        self.spider.wait.until.side_effect = TimeoutException("No elements found")

        results = list(
            self.spider.parse_search_results("廻天のアルバス", series_index=0)
        )

        # Should yield one empty item with series_name
        self.assertEqual(len(results), 1, "Should yield one item on timeout")
        self.assertIn("series_name", results[0])

    def test_parse_search_results_skips_old_releases(self):
        """Test that parse_search_results() skips books with old release dates."""
        self.spider.last_release_dates = ["2025-12-18"]

        # Mock link elements
        mock_link1 = MagicMock()
        mock_link2 = MagicMock()

        # Mock release date elements - both older than last_release_dates
        mock_date1 = MagicMock()
        mock_date1.get_attribute.return_value = "発売日：2025年12月15日"
        mock_date2 = MagicMock()
        mock_date2.get_attribute.return_value = "発売日：2025年12月16日"

        self.spider.wait.until.side_effect = [
            [mock_link1, mock_link2],  # First call: links
            [mock_date1, mock_date2],  # Second call: dates
            TimeoutException(
                "No next page"
            ),  # Next page button not found (since all links skipped)
        ]

        results = list(
            self.spider.parse_search_results("廻天のアルバス", series_index=0)
        )

        # Should skip all links due to old dates
        self.assertEqual(
            len(results), 0, "Should skip all links with old release dates"
        )


class TestBooksJpSpiderParseDetailInfo(unittest.TestCase):
    """Test cases for the parse_detail_info() method of BooksJpSpider."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.books_jp.webdriver"):
            self.spider = BooksJpSpider()
            self.spider.topic = "series_name"
            self.spider.target_info = "//span[@class='bookdetail_title_text']"

            # Mock driver and wait
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/book/123"
            self.spider.wait = MagicMock()

    def test_parse_detail_info_extracts_all_fields(self):
        """Test that parse_detail_info() extracts all book information correctly."""
        # Create item
        item = JpComicItem()
        item["series_name"] = "廻天のアルバス"

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
            # Match multiple author elements including series info
            mock_elem1 = MagicMock()
            mock_elem1.get_attribute.return_value = ""
            mock_elem2 = MagicMock()
            mock_elem2.get_attribute.return_value = "少年サンデーコミックス"
            mock_elem3 = MagicMock()
            mock_elem3.get_attribute.return_value = "原案：牧 彰久"
            mock_elem4 = MagicMock()
            mock_elem4.get_attribute.return_value = "絵：箭坪 幹"
            return [mock_elem1, mock_elem2, mock_elem3, mock_elem4]

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
        # Create item
        item = JpComicItem()
        item["series_name"] = "廻天のアルバス"

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
        # Create item
        item = JpComicItem()
        item["series_name"] = "廻天のアルバス"

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


class TestBooksJpSpiderClosed(unittest.TestCase):
    """Test cases for the closed() method of BooksJpSpider."""

    @patch("comic_scrapers.spiders.books_jp.webdriver")
    def test_closed_quits_driver(self, mock_webdriver):
        """Test that closed() method quits the Selenium driver."""
        spider = BooksJpSpider()
        mock_driver = MagicMock()
        spider.driver = mock_driver

        spider.closed("finished")

        mock_driver.quit.assert_called_once()

    @patch("comic_scrapers.spiders.books_jp.webdriver")
    def test_closed_handles_no_driver_attribute(self, mock_webdriver):
        """Test that closed() handles missing driver attribute gracefully."""
        spider = BooksJpSpider()
        # Delete driver attribute
        if hasattr(spider, "driver"):
            delattr(spider, "driver")

        # Should not raise exception
        spider.closed("finished")

    @patch("comic_scrapers.spiders.books_jp.webdriver")
    def test_closed_handles_none_driver(self, mock_webdriver):
        """Test that closed() handles None driver gracefully."""
        spider = BooksJpSpider()
        spider.driver = None

        # Should not raise exception
        spider.closed("finished")


class TestBooksJpTitleTwSpiderIntegration(unittest.TestCase):
    """Integration tests for BooksJpTitleTwSpider."""

    @patch("comic_scrapers.spiders.books_jp.Series")
    @patch("comic_scrapers.spiders.books_jp.webdriver")
    def test_books_jp_title_spider_initialization(self, mock_webdriver, mock_series):
        """Test BooksJpTitleTwSpider initializes with correct topic & topic_list."""
        # Mock datetime objects for dates
        from datetime import datetime

        mock_date1 = datetime(2025, 12, 18)
        mock_date2 = datetime(2025, 12, 17)

        # Mock Series.objects query - need to mock the full chain
        mock_queryset = MagicMock()
        mock_annotated = MagicMock()
        mock_series.objects.filter.return_value = mock_queryset
        mock_queryset.values_list.return_value = ["廻天のアルバス", "ブルーピリオド"]
        mock_queryset.annotate.return_value = mock_annotated
        mock_annotated.values_list.return_value = [mock_date1, mock_date2]

        spider = BooksJpTitleTwSpider()

        self.assertEqual(spider.name, "booksjp_title")
        self.assertEqual(spider.topic, "series_name")
        self.assertEqual(len(spider.topic_list), 2)
        self.assertIn("廻天のアルバス", spider.topic_list)

    @patch("comic_scrapers.spiders.books_jp.Series")
    @patch("comic_scrapers.spiders.books_jp.webdriver")
    def test_books_jp_title_spider_target_info_xpath(self, mock_webdriver, mock_series):
        """Test that BooksJpTitleTwSpider sets correct target_info xpath."""
        # Mock Series.objects query - need to mock the full chain
        mock_queryset = MagicMock()
        mock_annotated = MagicMock()
        mock_series.objects.filter.return_value = mock_queryset
        mock_queryset.values_list.return_value = []
        mock_queryset.annotate.return_value = mock_annotated
        mock_annotated.values_list.return_value = []

        spider = BooksJpTitleTwSpider()

        self.assertEqual(
            spider.target_info,
            "//span[@class='bookdetail_title_text']",
            "Should use bookdetail_title_text for series name searches",
        )

    @patch("comic_scrapers.spiders.books_jp.Series")
    @patch("comic_scrapers.spiders.books_jp.webdriver")
    def test_books_jp_title_spider_empty_series_list(self, mock_webdriver, mock_series):
        """Test that BooksJpTitleTwSpider handles empty series list."""
        # Mock Series.objects query - need to mock the full chain
        mock_queryset = MagicMock()
        mock_annotated = MagicMock()
        mock_series.objects.filter.return_value = mock_queryset
        mock_queryset.values_list.return_value = []
        mock_queryset.annotate.return_value = mock_annotated
        mock_annotated.values_list.return_value = []

        spider = BooksJpTitleTwSpider()

        self.assertEqual(len(spider.topic_list), 0)
        self.assertEqual(len(spider.last_release_dates), 0)


class TestBooksJpSpiderSearchButtonClick(unittest.TestCase):
    """Test cases for search button click functionality in parse() method."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("comic_scrapers.spiders.books_jp.webdriver"):
            self.spider = BooksJpSpider()
            self.spider.topic = "series_name"
            self.spider.topic_list = ["廻天のアルバス"]

            # Mock driver and its methods
            self.spider.driver = MagicMock()
            self.spider.driver.current_url = "https://www.books.or.jp/"

    def test_parse_clicks_search_button(self):
        """Test that parse() clicks the search button after entering query."""
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

        # Mock parse_search_results to avoid actual processing
        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            list(self.spider.parse(response))

            # Verify search button was clicked
            mock_search_button.click.assert_called()

    def test_parse_sends_keys_to_search_box(self):
        """Test that parse() sends the topic to search box."""
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

        # Mock parse_search_results to avoid actual processing
        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            list(self.spider.parse(response))

            # Verify topic was sent to search box
            calls = [str(call) for call in mock_search_box.send_keys.call_args_list]
            topic_sent = any("廻天のアルバス" in str(call) for call in calls)
            self.assertTrue(topic_sent, "Should send topic to search box")

    def test_parse_clears_search_box_before_typing(self):
        """Test that parse() clears search box before entering new query."""
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

        # Mock parse_search_results to avoid actual processing
        with patch.object(self.spider, "parse_search_results", return_value=iter([])):
            url = "https://www.books.or.jp/"
            request = Request(url=url)
            response = HtmlResponse(
                url=url, request=request, body=b"<html></html>", encoding="utf-8"
            )

            list(self.spider.parse(response))

            # Verify search box was cleared (Ctrl+A and DELETE sent)
            self.assertGreater(
                mock_search_box.send_keys.call_count,
                2,
                "Should send multiple keys including clear commands",
            )


if __name__ == "__main__":
    unittest.main()
