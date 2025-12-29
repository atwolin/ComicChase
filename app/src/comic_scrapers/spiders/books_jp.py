from scrapy.item import Item
from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.common.by import By

from comic_scrapers.items import JpComicItem
from comic_scrapers.spiders.base_selenium_spider import BaseSeleniumSpider


class BooksJpSpider(BaseSeleniumSpider):
    """Spider to scrape Japanese book information from books.or.jp site.

    This spider obtain book urls and extracts volume information
    such as author, release date, and publisher.
    """

    name = "books_jp"
    allowed_domains = ["books.or.jp"]
    start_urls = ["https://www.books.or.jp/"]

    # ========================================================================
    # Abstract properties implementation
    # ========================================================================

    @property
    def search_input_xpath(self) -> str:
        """XPath for the search input field."""
        return "//input[@id='searchforbooks_title']"

    @property
    def search_results_url_xpath(self) -> str:
        """XPath for book URLs in search results."""
        return "//a[@class='result_list_button']"

    @property
    def search_results_date_xpath(self) -> str:
        """XPath for release dates in search results."""
        return "//div[@class='result_list_discription_publishdate']"

    @property
    def next_page_button_xpath(self) -> str:
        """XPath for the next page button in search results."""
        return "//button[@aria-label='1ページ後に進む']"

    def create_item(self) -> Item:
        """Create and return a JpComicItem."""
        return JpComicItem()

    def extract_detail_fields(self, item: Item) -> Item:
        """Extract detail fields from books.or.jp book page."""
        # Series fields
        title_jp = self.driver.find_element(
            By.XPATH, "//span[@class='bookdetail_title_text']"
        ).text
        author_jp = self.driver.find_elements(
            By.XPATH, "//div[@class='bookdetail_author']"
        )

        # Volume fields
        publisher_jp = self.driver.find_element(
            By.XPATH, "//div[@class='bookdetail_publisher']"
        ).text

        item["title_jp"] = title_jp.strip()
        item["author_jp"] = [
            element.get_attribute("innerHTML").strip() for element in author_jp
        ]
        item["publisher_jp"] = publisher_jp.strip()

        return item

    # ========================================================================
    # Hook methods override
    # ========================================================================

    def perform_search(self, search_box, topic_item: str):
        """Execute the search using books.or.jp specific search button."""
        search_box.click()

        # Clear the search box
        import time

        from selenium.webdriver.common.keys import Keys

        search_box.send_keys(Keys.CONTROL + "a")  # Select all
        search_box.send_keys(Keys.DELETE)  # Delete
        time.sleep(0.5)  # Brief wait for field to clear
        search_box.send_keys(topic_item)
        search_box.send_keys(Keys.RETURN)

        # Click the search button
        search_button_xpath = "//button[@class='searchforbooks_search_button']"
        search_button = self.driver.find_element(By.XPATH, search_button_xpath)
        search_button.click()

    def should_skip_detail_page(self, page_value: str, product_desc: str) -> bool:
        """Check if book is an e-book or doesn't match search query.

        Args:
            page_value: The value extracted from the detail page (e.g., series name).
            product_desc: Product description for additional validation.

        Returns:
            bool: True if this page should be skipped (e-book or doesn't match).
        """
        if not page_value or not product_desc:
            return False

        search_value = (
            getattr(self, self.search_field_name, None)
            if self.search_field_name
            else None
        )
        # Skip if search value doesn't match or if it's an e-book
        return (search_value and search_value not in page_value) or (
            "JP-eコード" in product_desc
        )

    def has_more_pages(self, prev_url: str | None, current_url: str) -> bool:
        """Check if there are more pages to process.

        books.or.jp uses JavaScript pagination, so URL doesn't change.
        We always return True here and rely on the next button timeout to stop.

        Args:
            prev_url: URL of the previous page (None for first page).
            current_url: URL of the current page.

        Returns:
            bool: Always True for books.or.jp (URL never changes).
        """
        # For books.or.jp, URL doesn't change between pages
        # We rely on TimeoutException when next button is not found
        return True

    def wait_for_page_change(self, prev_url: str) -> bool:
        """Wait for page content to change after clicking next button.

        Since URL doesn't change on books.or.jp, we wait for search results
        to become stale (indicating page refresh).

        Args:
            prev_url: URL before clicking next button (not used for books.or.jp).

        Returns:
            bool: True if page content changed, False if timeout.
        """
        try:
            # Wait for the search results container to update
            # We detect this by waiting for the old results to become stale
            from selenium.webdriver.support import expected_conditions as EC

            # Get current results before they become stale
            old_results = self.driver.find_elements(
                By.XPATH, self.search_results_url_xpath
            )
            if old_results:
                # Wait for first result to become stale (page refreshed)
                self.wait.until(EC.staleness_of(old_results[0]))
                return True

            # Fallback: wait for new results to appear
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, self.search_results_url_xpath)
                )
            )
            return True
        except selenium_exceptions.TimeoutException:
            return False

    @property
    def product_desc_xpath(self) -> str:
        """XPath for product description on books.or.jp."""
        return "//div[@class='otherdata']"


class BooksJpTitleTwSpider(BooksJpSpider):
    """Spider to scrape Japanese book information from books.or.jp site
    by Japanese series name."""

    name = "booksjp_title"

    def __init__(self, search_value, last_release_date=None, *args, **kwargs):
        """Initialize the spider to search by Japanese title.

        Args:
            search_value (str): Single Japanese title to search for.
            last_release_date (str, optional): Last known release date for this title
                in YYYY-MM-DD format. Used to skip volumes we already have.
                Defaults to None (crawl all volumes).
        """
        super().__init__(
            search_value=search_value,
            last_release_date=last_release_date,
            *args,
            **kwargs,
        )

        # Search by series name
        self.search_field_name = "title_jp"

        # Verification configuration
        self.verify_element_xpath = "//span[@class='bookdetail_title_text']"

        if not search_value:
            raise ValueError(
                "search_value (title_jp) is required for BooksJpTitleTwSpider"
            )

        self.logger.info(
            f"BooksJpTitleTwSpider: Searching for title: {search_value}"
            f" (last release: {last_release_date})"
        )
