from scrapy.item import Item
from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from comic_scrapers.items import OrphanMapItem
from comic_scrapers.spiders.base_selenium_spider import BaseSeleniumSpider


class EsliteSpider(BaseSeleniumSpider):
    """Spider to scrape taiwan-version book information from eslite.com site.

    This spider targets the new releases section to obtain book urls
    and extracts volume information such as author, release date, and publisher.
    """

    name = "eslite_base"
    allowed_domains = ["eslite.com"]
    start_urls = ["https://www.eslite.com"]

    # ========================================================================
    # Abstract properties implementation
    # ========================================================================

    @property
    def search_input_xpath(self) -> str:
        """XPath for the search input field."""
        return "//input[@name='query']"

    @property
    def search_results_url_xpath(self) -> str:
        """XPath for book URLs in search results."""
        return "//div[@class='item-wording-wrap']//a[@data-gid='title-link']"

    @property
    def search_results_date_xpath(self) -> str:
        """XPath for release dates in search results."""
        return "//div[@class='product-date mr-1']"

    @property
    def next_page_button_xpath(self) -> str:
        """XPath for the next page button in search results."""
        return "//div[@class='page-number']/div[@data-gid='pagination-next']"

    def create_item(self) -> Item:
        """Create and return an OrphanMapItem."""
        return OrphanMapItem()

    def extract_detail_fields(self, item: Item) -> Item:
        """Extract detail fields from eslite.com book page."""
        # Series fields
        title_jp = self.driver.find_element(
            By.XPATH, "//h4[@class='local-fw-normal font-normal text-gray-400']"
        ).text
        title_tw = self.driver.find_element(
            By.XPATH, "//h1[@class='sans-font-semi-bold']"
        ).text
        # Updated XPath for author (now in a link with data-test-id)
        author_tw = self.driver.find_element(
            By.XPATH, "//a[@data-test-id='author-link']"
        ).text

        # Volume fields
        release_date_tw = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'books-publication-row')]"
            "//span[contains(text(), '/')]",
        ).text
        publisher_tw = self.driver.find_element(
            By.XPATH, "//a[@data-test-id='supplier-link']"
        ).text
        image_element = self.driver.find_element(
            By.XPATH, "//div[contains(@class, 'item-image-wrap')]//img"
        ).get_attribute("src")

        item["title_jp"] = title_jp.strip()
        item["title_tw"] = title_tw.strip()
        item["author_tw"] = author_tw.strip()
        item["release_date_tw"] = release_date_tw.strip()
        item["publisher_tw"] = publisher_tw.strip()
        item["image_url_tw"] = image_element.strip() if image_element else ""

        return item

    # ========================================================================
    # Hook methods override
    # ========================================================================

    def apply_search_filters(self, is_first_page: bool):
        """Apply category filter on first page of search results."""
        if is_first_page:
            try:
                category_tw = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//span[@class='desc' and text()='中文書']")
                    )
                )
                # Use JavaScript click to avoid ElementClickInterceptedException
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", category_tw
                )
                self.driver.execute_script("arguments[0].click();", category_tw)
                # Wait for filter to be applied (search results to reload)
                self.wait.until(EC.staleness_of(category_tw))

            except selenium_exceptions.TimeoutException:
                self.logger.warning(
                    "apply_search_filters(): Timeout while applying category filter. "
                    "This may occur if no search results are found "
                    "or the page structure changed."
                )

    def should_skip_detail_page(self, page_value: str, product_desc: str) -> bool:
        """Check if the page value matches the search query.

        Args:
            page_value: The value extracted from the detail page (e.g., book title).
            product_desc: Product description for additional validation (currently
            unused, reserved for future validation logic).

        Returns:
            bool: True if this page should be skipped (doesn't match search criteria).
        """
        if not page_value:
            return False
        search_value = (
            getattr(self, self.search_field_name, None)
            if self.search_field_name
            else None
        )
        if not search_value:
            return False
        return search_value not in page_value

    @property
    def product_desc_xpath(self) -> str:
        """XPath for product description on eslite.com."""
        return "//div[@class='product-description-schema']"


class EsliteISBNSpider(EsliteSpider):
    """Spider to scrape Taiwanese book information from eslite.com by book ISBN."""

    name = "eslite_isbn"

    def __init__(self, search_value, last_release_date=None, *args, **kwargs):
        """Initialize the spider to search by ISBN.

        Args:
            search_value (str): Single ISBN to search for.
            last_release_date (str): Last known release date for this ISBN
                in YYYY-MM-DD format (optional for ISBN search).
        """
        kwargs["search_value"] = search_value
        kwargs["last_release_date"] = last_release_date
        super().__init__(*args, **kwargs)

        # Search by ISBN
        self.search_field_name = "isbn_tw"

        # Verification configuration
        self.verify_element_xpath = "//div[@class='product-description-schema']"

        if not search_value:
            raise ValueError("search_value (ISBN) is required for EsliteISBNSpider")

        self.logger.info(f"EsliteISBNSpider: Searching for ISBN: {search_value}")


class EsliteTitleTwSpider(EsliteSpider):
    """Spider to scrape Taiwanese book information from eslite.com by book title."""

    name = "eslite_title_tw"

    def __init__(self, search_value, last_release_date=None, *args, **kwargs):
        """Initialize the spider to search by Taiwanese title.

        Args:
            search_value (str): Single Taiwanese title to search for.
            last_release_date (str, optional): Last known release date for this title
                in YYYY-MM-DD format. Used to skip volumes we already have.
                Defaults to None (crawl all volumes).
        """
        kwargs["search_value"] = search_value
        kwargs["last_release_date"] = last_release_date
        super().__init__(*args, **kwargs)

        # Search by title
        self.search_field_name = "title_tw"

        # Verification configuration
        self.verify_element_xpath = "//h1[@class='sans-font-semi-bold']"

        if not search_value:
            raise ValueError(
                "search_value (title_tw) is required for EsliteTitleTwSpider"
            )

        self.logger.info(
            f"EsliteTitleTwSpider: Searching for title: {search_value}"
            f" (last release: {last_release_date})"
        )
