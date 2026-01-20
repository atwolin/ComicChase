import os
import re
import time
from abc import ABC, abstractmethod

import scrapy
from scrapy.http import HtmlResponse
from scrapy.item import Item
from selenium import webdriver
from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseSeleniumSpider(scrapy.Spider, ABC):
    """Abstract base spider for scraping book sites using Selenium WebDriver.

    This base class provides common functionality for spiders that need to:
    - Use Selenium for JavaScript-heavy sites
    - Search for multiple values (titles, ISBNs, series names)
    - Parse search results with pagination support
    - Extract detailed book information from detail pages
    - Handle release date filtering to avoid re-scraping old data
    - Verify page content matches search criteria

    Design Pattern:
        Template Method Pattern - defines the skeleton of the scraping algorithm,
        allowing subclasses to customize specific steps through hook methods.

    Configuration:
        Subclasses must implement abstract properties for XPath selectors and
        abstract methods for item creation and field extraction.

    Search Configuration Attributes:
        search_field_name (str): Name of the field being searched
        search_value_list (list): List of values to search for
        verify_element_xpath (str): XPath to extract value for page verification
        last_release_dates (list): Last known release dates for filtering

    Hook Methods (override to customize behavior):
        - perform_search(): Customize search box interaction
        - apply_search_filters(): Add site-specific filters
        - should_skip_detail_page(): Decide if a detail page should be skipped
        - has_more_pages(): Check if pagination should continue
        - wait_for_page_change(): Wait for page navigation completion
    """

    allowed_domains = []
    start_urls = []

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.selectreactor.SelectReactor",
        "DOWNLOAD_DELAY": 10,  # Polite crawling: 10 seconds between requests
    }

    # Delay after processing each detail page (seconds)
    detail_page_delay = 20

    DATE_REGEX = re.compile(r"([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日")

    def __init__(self, search_value=None, last_release_date=None, *args, **kwargs):
        """Initialize the spider with Selenium WebDriver.

        Supports two modes based on SELENIUM_HUB_URL environment variable:
        - Remote mode: Connects to Selenium Grid (local Docker Compose)
        - Local mode: Uses local ChromeDriver (Cloud Run environment)

        Args:
            search_value (str): Single search value (e.g., title, ISBN) to crawl.
            last_release_date (str): Last known release date for this search value
                in YYYY-MM-DD format. Used to filter out old volumes.
        """
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        # Check environment variable to determine WebDriver mode
        selenium_hub_url = os.getenv("SELENIUM_HUB_URL", "")

        if selenium_hub_url:
            # development: Connect to Selenium Grid (local development)
            self.logger.info(f"Using Remote WebDriver: {selenium_hub_url}")
            self.driver = webdriver.Remote(
                command_executor=selenium_hub_url, options=chrome_options
            )
        else:
            # production: Use local ChromeDriver (Cloud Run)
            chrome_options.add_argument("--headless")  # Headless mode for cloud
            chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless
            self.logger.info("Using Local ChromeDriver")
            self.driver = webdriver.Chrome(options=chrome_options)

        self.wait = WebDriverWait(self.driver, 10)

        # Search configuration
        self.search_field_name = (
            None  # Field name to search by (e.g., "title_tw", "isbn_tw")
        )
        self.search_value = search_value  # Single value to search for

        # Verification configuration
        self.verify_element_xpath = None  # XPath to extract value for verification

        # Filtering configuration
        self.last_release_date = last_release_date  # Last release date for filtering

    # ========================================================================
    # Abstract properties - must be implemented by subclasses
    # ========================================================================

    @property
    @abstractmethod
    def search_input_xpath(self) -> str:
        """XPath for the search input field."""
        pass

    @property
    @abstractmethod
    def search_results_url_xpath(self) -> str:
        """XPath for book URLs in search results."""
        pass

    @property
    @abstractmethod
    def search_results_date_xpath(self) -> str:
        """XPath for release dates in search results."""
        pass

    @property
    @abstractmethod
    def next_page_button_xpath(self) -> str:
        """XPath for the next page button in search results."""
        pass

    @property
    @abstractmethod
    def product_desc_xpath(self) -> str:
        """XPath for the product description element on detail page."""
        pass

    @abstractmethod
    def create_item(self) -> Item:
        """Create and return an empty item for this spider.

        Returns:
            Item: A new item instance (e.g., OrphanMapItem, JpComicItem).
        """
        pass

    @abstractmethod
    def extract_detail_fields(self, item: Item) -> Item:
        """Extract book details from the current page and populate the item.

        This method should use self.driver to find elements on the detail page
        and populate the item with extracted data.

        Args:
            item (Item): The item to populate with extracted data.

        Returns:
            Item: The populated item.
        """
        pass

    # ========================================================================
    # Hook methods - can be overridden by subclasses if needed
    # ========================================================================

    def perform_search(self, search_box, topic_item: str):
        """Execute the search for a topic item.

        Default implementation clears the search box and sends the query.
        Override if site requires different search behavior.

        Args:
            search_box: The WebElement for the search input.
            topic_item (str): The search query.
        """
        search_box.click()

        # Clear the search box
        search_box.send_keys(Keys.CONTROL + "a")  # Select all
        search_box.send_keys(Keys.DELETE)  # Delete
        search_box.send_keys(topic_item)
        search_box.send_keys(Keys.RETURN)

    def apply_search_filters(self, is_first_page: bool):
        """Apply any search filters (e.g., category filters).

        Override this method if the site requires filtering.
        Default implementation does nothing.

        Args:
            is_first_page (bool): True if this is the first page of results.
        """
        pass

    def should_skip_detail_page(self, page_value: str, product_desc: str) -> bool:
        """Determine if the detail page should be skipped.

        Override to implement custom validation logic.

        Args:
            page_value: The value extracted from the detail page
            product_desc: Product description content.

        Returns:
            bool: True if this page should be skipped (doesn't match search criteria).
        """
        if not self.search_field_name or not page_value:
            return False
        return self.search_field_name not in page_value

    def has_more_pages(self, prev_url: str | None, current_url: str) -> bool:
        """Check if there are more pages to process.

        Default implementation checks if URL has changed.
        Override this for sites where URL doesn't change during pagination.

        Args:
            prev_url: URL of the previous page (None for first page).
            current_url: URL of the current page.

        Returns:
            bool: True if should continue to next page, False if this is a repeat.
        """
        if prev_url is None:
            return True  # First page, always process
        return prev_url != current_url  # Default: check if URL changed

    def wait_for_page_change(self, prev_url: str) -> bool:
        """Wait for page to change after clicking next button.

        Default implementation waits for URL to change.
        Override for sites where URL doesn't change (e.g., JavaScript pagination).

        Args:
            prev_url: URL before clicking next button.

        Returns:
            bool: True if page changed successfully, False if timeout.
        """
        try:
            # Wait for URL to change or page to update
            self.wait.until(lambda driver: driver.current_url != prev_url)
            return True
        except selenium_exceptions.TimeoutException:
            return False

    # ========================================================================
    # Template methods - common workflow implementation
    # ========================================================================

    def _get_book_release_date(self, product_desc: str) -> str | None:
        """Process product_desc to extract release date.

        Uses regex to extract date components in format YYYY年MM月DD日
        and reformats to YYYY-MM-DD.

        Args:
            product_desc (str): The product description containing the release date.

        Returns:
            str | None: The release date in YYYY-MM-DD format, or None if not found.
        """
        match = self.DATE_REGEX.search(product_desc)
        if match:
            year, month, day = match.groups()
            # Pad month and day with leading zeros to ensure 2 digits
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None

    def start_requests(self):
        """Load the homepage and start parsing.

        Yields:
            Generator: Yields from parse() method.
        """
        url = self.start_urls[0]
        # Load the homepage
        self.driver.get(url)
        # Wait for page to be ready
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        self.logger.debug(f"start_requests(): Loaded homepage {url}")

        response = HtmlResponse(
            url=self.driver.current_url,
            body=self.driver.page_source,
            encoding="utf-8",
            request=scrapy.Request(url=url),
        )
        yield from self.parse(response)

    def parse(self, response: HtmlResponse):
        """Parse the homepage and perform search for the configured search value.

        Args:
            response (HtmlResponse): Response object of the homepage.

        Yields:
            Item: Items extracted from search results.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found.
            NoSuchElementException: If expected HTML elements are not found.
            Exception: If any error occurs during parsing.
        """
        if not self.search_value:
            raise ValueError(
                f"{self.__class__.__name__} requires search_value to be set. "
                "Please provide search_value when initializing the spider."
            )

        self.logger.info(
            f"parse(): Processing {self.search_field_name}: {self.search_value}"
        )

        try:
            search_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, self.search_input_xpath))
            )
            self.perform_search(search_box, self.search_value)
            time.sleep(3)

            yield from self.parse_search_results(
                search_value=self.search_value, last_release_date=self.last_release_date
            )

            self.logger.info(f"parse(): Completed processing {self.search_value}")

        except selenium_exceptions.TimeoutException as e:
            self.logger.error(
                f"parse(): Timeout while processing"
                f" {self.search_field_name} {self.search_value}: {e}"
            )
        except selenium_exceptions.NoSuchElementException as e:
            self.logger.error(
                f"parse(): Element not found while processing"
                f" {self.search_field_name} {self.search_value}: {e}"
            )
        except selenium_exceptions.WebDriverException as e:
            self.logger.error(
                f"parse(): WebDriver error while processing"
                f" {self.search_field_name} {self.search_value}."
                f" Error type: {type(e).__name__}, Message: {e}",
                exc_info=True,
            )

    def parse_search_results(
        self,
        search_value: str,
        last_release_date: str | None = None,
        prev_url: str | None = None,
    ):
        """Parse the search results page to extract book detail URLs.

        Extracts book URLs and their release dates from the current search results page.
        Filters out books that are not newer than the last recorded release date.
        After processing all results on the current page, attempts to navigate to
        the next page if available.

        Args:
            search_value (str): The current search value being processed.
            last_release_date (str): Last known release date for this search value
                in YYYY-MM-DD format. Volumes with this date or older will be skipped.
            prev_url (str, optional): The URL of the previous search results page.
                Used to detect if pagination has reached the end.

        Yields:
            Item: Items containing the extracted information from detail pages.

        Raises:
            TimeoutException: If timeout occurs locating elements or next page button.
            WebDriverException: For other Selenium-related errors.

        Note:
            - Uses has_more_pages() hook to check if pagination should continue
            - Uses wait_for_page_change() hook after clicking next page
            - Refreshes element refs after each detail page to avoid stale elements
        """
        self.logger.debug(
            f"parse_search_results(): Parsing search results from"
            f" {self.driver.current_url}"
        )

        # Check if we've hit the same page (no more pages)
        if not self.has_more_pages(prev_url, self.driver.current_url):
            self.logger.info("No more pages to process (same page detected)")
            return

        # Apply filters (e.g., category filter) on first page
        is_first_page = prev_url is None
        self.apply_search_filters(is_first_page)

        # Wait for search results page to fully load
        time.sleep(2)

        # Get book detail urls and release dates
        urls = None
        volume_release_dates = None
        try:
            urls = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, self.search_results_url_xpath)
                )
            )
            volume_release_dates = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, self.search_results_date_xpath)
                )
            )
        except selenium_exceptions.TimeoutException as e:
            self.logger.error(
                f"parse_search_results(): Timeout while locating book urls for"
                f" {self.search_field_name} {search_value}: {e}"
            )
            # Create and yield empty item to track failed search
            item = self.create_item()
            if self.search_field_name:
                item[self.search_field_name] = search_value
            if hasattr(item, "search_url"):
                item["search_url"] = self.driver.current_url
            yield item
            return
        except selenium_exceptions.WebDriverException as e:
            self.logger.error(
                f"parse_search_results(): WebDriver error while locating book urls for"
                f" {self.search_field_name} {search_value}."
                f" Error type: {type(e).__name__}, Message: {e}",
                exc_info=True,
            )
            # Create and yield empty item to track failed search
            item = self.create_item()
            if self.search_field_name:
                item[self.search_field_name] = search_value
            if hasattr(item, "search_url"):
                item["search_url"] = self.driver.current_url
            yield item
            return

        self.logger.debug(
            f"parse_search_results(): Found {len(urls)} book urls"
            " on the search results page."
        )

        # Extract all data upfront to avoid stale element references
        # Store the HTML content of each date element, not the element itself
        release_date_texts = []
        for date_elem in volume_release_dates:
            try:
                release_date_texts.append(date_elem.get_attribute("innerHTML"))
            except selenium_exceptions.StaleElementReferenceException:
                release_date_texts.append(None)
                self.logger.warning(
                    "parse_search_results(): Stale element when extracting date text"
                )

        # Parse each book url
        n = len(urls)
        for i in range(n):
            # Skip if we already have this or newer volume
            current_release_date = None
            if i < len(release_date_texts) and release_date_texts[i]:
                current_release_date = self._get_book_release_date(
                    release_date_texts[i]
                )

            if current_release_date and last_release_date:
                if current_release_date <= last_release_date:
                    self.logger.debug(
                        f"parse_search_results(): Skipping url {i + 1}/{n}"
                        " - already have this volume\n"
                        f"current_release_date: {current_release_date},"
                        f" last_release_date: {last_release_date}"
                    )
                    continue

            self.logger.debug(f"parse_search_results(): Processing url {i + 1}/{n}")

            # Create a new item for each url
            item = self.create_item()
            item[f"{self.search_field_name}"] = search_value

            # Store the search value in search_query metadata field
            if "search_query" in item.fields:
                item["search_query"] = search_value

            if hasattr(item, "search_url"):
                item["search_url"] = self.driver.current_url

            yield from self.parse_detail_info(urls[i], item)

            # Wait for page to stabilize after returning from detail page
            time.sleep(2)

            self.logger.debug(
                f"parse_search_results(): Completed processing url {i + 1}/{n}"
            )
            # Refresh urls list after navigating back to avoid stale element reference
            try:
                urls = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, self.search_results_url_xpath)
                    )
                )
                # Wait for refreshed elements to be stable
                time.sleep(2)
            except selenium_exceptions.TimeoutException as e:
                self.logger.error(
                    f"parse_search_results(): Timeout while relocating search results"
                    f" after processing url {i + 1}/{n}. Error: {e}"
                )
                # Cannot continue processing this page if we can't find results
                break
            except selenium_exceptions.WebDriverException as e:
                self.logger.error(
                    "parse_search_results(): WebDriver error after "
                    f"processing url {i + 1}/{n}."
                    f" Error type: {type(e).__name__}, Message: {e}",
                    exc_info=True,  # Log full stack trace for debugging
                )
                # Selenium driver issue, cannot continue
                break

        # Try to go to next page
        prev_url = self.driver.current_url
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self.next_page_button_xpath))
            )
            next_button.click()

            # Wait for page to change
            if not self.wait_for_page_change(prev_url):
                self.logger.warning(
                    "parse_search_results(): Page may not have changed"
                    " after clicking next, continuing anyway"
                    f" for {self.search_field_name} {search_value}"
                )

            yield from self.parse_search_results(
                search_value, last_release_date, prev_url
            )
        except selenium_exceptions.TimeoutException as e:
            self.logger.error(
                "parse_search_results(): Timeout because no next button found"
                f" for {self.search_field_name} {search_value}: {e}"
            )

    def parse_detail_info(self, url, item: Item):
        """Extract series and volume information from the book URL.

        Navigates to the book detail page, verifies it matches the search criteria,
        and extracts detailed information by calling the abstract
        extract_detail_fields method.

        Args:
            url: The WebElement link to click to navigate to the detail page.
            item (Item): Item to populate with extracted information.

        Yields:
            Item: The populated item with extracted information.

        Raises:
            TimeoutException: If timeout occurs loading the detail page.
            NoSuchElementException: If expected HTML elements are not found.
            AttributeError: If attribute access fails during field extraction.
            WebDriverException: For other Selenium-related errors.

        Flow:
            1. Click URL to navigate to detail page
            2. Extract page value for verification (via verify_element_xpath)
            3. Extract product description
            4. Call should_skip_detail_page() hook to check if page should be skipped
            5. If not skipped, extract detail fields via extract_detail_fields()
            6. Navigate back to search results page
            7. Yield the populated item
        """
        self.logger.debug(
            f"parse_detail_info(): Parsing info from {self.driver.current_url}"
        )

        product_desc = None
        page_value = None
        try:
            time.sleep(3)
            url.click()
            # Extract value from page for verification
            page_value_xpath = self.verify_element_xpath
            page_value_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, page_value_xpath))
            )
            page_value = page_value_element.get_attribute("innerHTML")

            # Find product description element (may vary by site)
            product_desc_xpath = self.product_desc_xpath
            product_desc_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, product_desc_xpath))
            )
            product_desc = product_desc_element.get_attribute("innerHTML")

            if self.should_skip_detail_page(page_value, product_desc):
                self.driver.back()
                yield item
                return

        except selenium_exceptions.TimeoutException as e:
            self.logger.error(
                f"""
                parse_detail_info(): Timeout while checking detail page for
                {self.search_field_name} {item[f"{self.search_field_name}"]}\n
                page_value:          {page_value}\n
                product_desc:        {product_desc}\n
                error:               {e}
                """
            )
            self.driver.back()
            yield item
            return

        item["detail_url"] = self.driver.current_url
        try:
            # Extract site-specific fields
            item = self.extract_detail_fields(item)

            # Store product description if item has this field
            if "product_desc" in item.fields:
                item["product_desc"] = product_desc.strip()

            self.logger.info(
                f"parse_detail_info(): Successfully parsed info from"
                f" {self.driver.current_url}"
            )

        except selenium_exceptions.NoSuchElementException as e:
            self.logger.error(
                f"parse_detail_info(): Element not found on"
                f" {self.driver.current_url}: {e}"
            )
        except AttributeError as e:
            self.logger.error(
                f"parse_detail_info(): AttributeError parsing info"
                f" from {self.driver.current_url}: {e}"
            )
        except selenium_exceptions.WebDriverException as e:
            self.logger.error(
                f"parse_detail_info(): WebDriver error while parsing info from"
                f" {self.driver.current_url}."
                f" Error type: {type(e).__name__}, Message: {e}",
                exc_info=True,
            )

        finally:
            # Wait for detail page processing to complete
            # This long delay helps avoid triggering anti-scraping measures
            # and ensures the search results page is stable when we return
            time.sleep(self.detail_page_delay)

            # Go back to search results page
            self.driver.back()
            yield item

    def closed(self, reason):
        """Clean up Selenium driver when spider closes.

        Args:
            reason: The reason for spider closure.
        """
        self.logger.info("Closing Selenium driver...")
        if hasattr(self, "driver") and self.driver:
            try:
                self.driver.quit()
            except (KeyboardInterrupt, SystemExit):
                # Re-raise critical system exceptions
                raise
            except Exception as e:
                # Log and suppress all other exceptions during cleanup
                self.logger.warning(f"Error while quitting driver: {e}")
        self.logger.info("Selenium driver closed.")
