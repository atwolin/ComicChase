"""Unit tests for BaseSeleniumSpider.

Test Types:
-----------
- **Unit Tests**: Test individual methods/logic with all dependencies mocked.
  Focus on base class functionality that all spiders inherit.

Test Execution:
---------------
- All tests use mocked WebDriver and responses
- No real network requests or browser operations
- Fast execution suitable for CI/CD

Coverage:
---------
- Lifecycle management (driver cleanup)
- Future: pagination logic, hook methods, date parsing
"""

import unittest
from unittest.mock import MagicMock, patch

from comic_scrapers.spiders.eslite import EsliteSpider


class TestBaseSeleniumSpiderClosed(unittest.TestCase):
    """[UNIT] Test closed() method behavior.

    Tests the driver cleanup functionality inherited by all Selenium spiders.
    This is tested once here rather than in each spider's test file.
    """

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_closed_quits_driver(self, mock_webdriver):
        """Test that closed() method quits the Selenium driver."""
        spider = EsliteSpider(search_value="test_value")
        mock_driver = MagicMock()
        spider.driver = mock_driver

        spider.closed("finished")

        mock_driver.quit.assert_called_once()

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_closed_handles_none_driver(self, mock_webdriver):
        """Test that closed() handles None driver gracefully."""
        spider = EsliteSpider(search_value="test_value")
        spider.driver = None

        # Should not raise exception
        spider.closed("finished")

    @patch("comic_scrapers.spiders.base_selenium_spider.webdriver")
    def test_closed_handles_driver_quit_exception(self, mock_webdriver):
        """Test that closed() handles exception during driver.quit()."""
        spider = EsliteSpider(search_value="test_value")
        mock_driver = MagicMock()
        mock_driver.quit.side_effect = Exception("Quit failed")
        spider.driver = mock_driver

        # Should not raise exception
        spider.closed("finished")


if __name__ == "__main__":
    unittest.main()
