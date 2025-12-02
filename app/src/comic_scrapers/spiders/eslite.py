import re
import time

import scrapy
import selenium
from comic.models import Series, Volume
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comic_scrapers.items import OrphanMapItem


class EsliteSpider(scrapy.Spider):
    """Spider to scrape taiwan-version book information from eslite.com site.

    This spider targets the new releases section to obtain book urls
    and extracts volume information such as author, release date, and publisher.
    """

    name = "eslite_base"
    allowed_domains = ["eslite.com"]
    start_urls = ["https://www.eslite.com"]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.selectreactor.SelectReactor",
    }

    def __init__(self, *args, **kwargs):
        """See base class."""
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        self.driver = webdriver.Remote(
            command_executor="http://selenium:4444/wd/hub", options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        self.topic = None
        self.topic_list = None
        self.target_info = None
        self.last_release_dates = None

    DATE_REGEX = re.compile(r"([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日")

    def _get_book_release_date(self, product_desc: str):
        """Process product_desc to extract release date for the current volume.

        Because the date format in eslite.com.tw is in Chinese,
        we use a regex to extract the date components and reformat them to YYYY-MM-DD.
        Example formats:
            "2025年12月18日\n" -> "2025-12-18"
            "2018年12月06日\n" -> "2018-12-06"

        Args:
            product_desc (str): The product description string containing
                                the release date.

        Returns:
            str: The release date in YYYY-MM-DD format.
        """
        match = self.DATE_REGEX.search(product_desc)
        if match:
            year, month, day = match.groups()
            # Pad month and day with leading zeros to ensure 2 digits
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None

    def start_requests(self):
        """See base class."""
        url = self.start_urls[0]
        # Load the homepage without waiting for a specific element
        self.driver.get(url)
        time.sleep(2)

        self.logger.debug(f"start_requests(): Loaded homepage {url}")

        response = HtmlResponse(
            url=self.driver.current_url,
            body=self.driver.page_source,
            encoding="utf-8",
            request=scrapy.Request(url=url),
        )
        yield from self.parse(response)

    def parse(self, response: HtmlResponse):
        """Parse the homepage and perform searches for each topic item.

        Args:
            response (HtmlResponse): Response object of the homepage.

        Yields:
            OrphanMapItem: Item containing the extracted mapping information.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found.
            NoSuchElementException: If expected HTML elements are not found.
            Exception: If any error occurs during parsing.
        """
        self.logger.debug(f"parse(): Start parsing from {response.url}")

        input_xpath = "//input[@name='query']"

        for i, topic_item in enumerate(self.topic_list):
            # # TESTING: Stop after processing first 3 items
            # if i == 2:
            #     break
            # # END TESTING

            try:
                self.logger.debug(
                    f"parse(): Processing {self.topic} {topic_item}"
                    f"({i + 1}/{len(self.topic_list)})"
                )

                search_box = self.driver.find_element(By.XPATH, input_xpath)
                search_box.click()

                # Clear the search box
                search_box.send_keys(Keys.CONTROL + "a")  # Select all
                search_box.send_keys(Keys.DELETE)  # Delete
                time.sleep(0.5)  # Brief wait for field to clear

                # Send the search query
                search_box.send_keys(topic_item)
                search_box.send_keys(Keys.RETURN)

                # Wait for search results page to load before parsing
                time.sleep(3)

                yield from self.parse_search_results(topic_item, i)
                time.sleep(2)

                self.logger.debug(
                    f"parse(): Completed processing item {topic_item}"
                    f"({i + 1}/{len(self.topic_list)})"
                )

            except selenium.common.exceptions.TimeoutException as e:
                self.logger.error(
                    f"parse(): Timeout while processing"
                    f"{self.topic} {topic_item}: {e}"
                )
            except selenium.common.exceptions.NoSuchElementException as e:
                self.logger.error(
                    f"parse(): Element not found while processing"
                    f"{self.topic} {topic_item}: {e}"
                )
            except Exception as e:
                self.logger.error(
                    f"parse(): Failed to process {self.topic} {topic_item},"
                    f"error: {str(e)}",
                    exc_info=True,
                )

    def parse_search_results(
        self, topic_item: str, series_index: int, prev_url: str = None
    ):
        """Parse the search results page to extract book detail urls.

        Parse each search results page to find book detail urls and their release dates.
        If a book's release date is not newer than the last recorded release date,
        it will be skipped.

        Args:
            topic_item (str): The current topic item being processed.
            series_index (int): The index of the series in topic_list.
            prev_url (str, optional): The URL of the previous search results page.

        Yields:
            OrphanMapItem: Item containing the extracted mapping information.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found
                              or no more pages are found.
        """
        self.logger.debug(
            f"parse_search_results(): Parsing search results from"
            f"{self.driver.current_url}"
        )
        if prev_url == self.driver.current_url:
            self.logger.info("No more pages to process")
            return

        time.sleep(2)
        # Only click category filter on the first page (when prev_url is None)
        if prev_url is None:
            try:
                category_tw = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@title='中文書']"))
                )
                category_tw.click()
                time.sleep(2)
            except selenium.common.exceptions.TimeoutException as e:
                self.logger.error(
                    f"parse_search_results(): Timeout while applying category filter"
                    f"for {self.topic} {topic_item}: {e}"
                )

        # Get book detail urls
        urls_xpath = "//a[@class='item-image-url']"
        urls = None
        volume_release_date_xpath = "//div[@class='product-date mr-1']"
        volume_release_dates = None
        try:
            urls = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, urls_xpath))
            )
            volume_release_dates = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, volume_release_date_xpath)
                )
            )
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(
                f"parse_search_results(): Timeout while locating book urls for"
                f"{self.topic} {topic_item}: {e}"
            )
            # Create and yield empty item to track failed search
            item = OrphanMapItem()
            item[f"{self.topic}"] = topic_item
            item["search_url"] = self.driver.current_url
            yield item
            return
        self.logger.debug(
            f"parse_search_results(): Found {len(urls)} book urls"
            "on the search results page."
        )

        # Parse each book url
        n = len(urls)
        for i in range(n):
            # # TESTING: Stop after processing first 3 urls
            # if i == 2:
            #     break
            # # END TESTING

            # Skip if we already have this or newer volume
            current_release_date = self._get_book_release_date(
                volume_release_dates[i].get_attribute("innerHTML")
            )
            if (
                current_release_date
                and self.last_release_dates
                and series_index is not None
                and series_index < len(self.last_release_dates)
            ):
                if current_release_date <= self.last_release_dates[series_index]:
                    self.logger.debug(
                        f"parse_search_results(): Skipping url {i + 1}/{n}"
                        "- already have this volume\n"
                        f"current_release_date: {current_release_date},"
                        f" last_release_date: {self.last_release_dates[series_index]}"
                    )
                    continue

            self.logger.debug(f"parse_search_results(): Processing url {i + 1}/{n}")

            # Create a new item for each url
            item = OrphanMapItem()
            item[f"{self.topic}"] = topic_item
            item["search_url"] = self.driver.current_url

            yield from self.parse_detail_info(urls[i], item)
            time.sleep(2)

            self.logger.debug(
                f"parse_search_results(): Completed processing url {i + 1}/{n}"
            )
            # Refresh urls list after navigating back to avoid stale element reference
            urls = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, urls_xpath))
            )
            time.sleep(2)

        # Go to next page
        # # TESTING: Stop after first page
        # return
        # # END TESTING

        prev_url = self.driver.current_url
        next_button_xpath = (
            "//div[@class='page-number']" "/div[@data-gid='pagination-next']"
        )
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, next_button_xpath))
            )
            next_button.click()
            time.sleep(2)
            yield from self.parse_search_results(topic_item, series_index, prev_url)
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(
                f"parse_search_results(): Timeout because no next button found for"
                f"{self.topic} {topic_item}: {e}"
            )

    def parse_detail_info(self, url, item: OrphanMapItem):
        """Extract series and volume information from the book URL.

        Retrieves the book detail page and extracts series author, book title,
        release date, publisher, and product description, which including ISBN.

        Args:
            url: The WebElement link to click to navigate to the detail page.
            item (OrphanMapItem): Item containing the extracted mapping information.

        Yields:
            OrphanMapItem: Item containing the extracted mapping information.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found.
            NoSuchElementException: If expected HTML elements are not found.
            AttributeError: If expected HTML elements for book information
                            are not found.
            Exception: If any error occurs during parsing.
        """
        self.logger.debug(
            f"parse_detail_info(): Parsing series info from"
            f"{self.driver.current_url}"
        )

        product_desc = None
        topic_prevent = None
        try:
            url.click()
            topic_prevent_xpath = self.target_info
            topic_prevent_webelement = self.wait.until(
                EC.presence_of_element_located((By.XPATH, topic_prevent_xpath))
            )
            topic_prevent = topic_prevent_webelement.get_attribute("innerHTML")
            category_xpath = "//a[@title='動漫畫／圖文']"
            self.wait.until(EC.presence_of_element_located((By.XPATH, category_xpath)))
            product_desc_xpath = "//div[@class='product-description-schema']"
            product_desc_webelement = self.wait.until(
                EC.presence_of_element_located((By.XPATH, product_desc_xpath))
            )
            product_desc = product_desc_webelement.get_attribute("innerHTML")
            if item[f"{self.topic}"] not in topic_prevent:
                self.driver.back()
                yield item
                return
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(f"""
                parse_detail_info(): Timeout while checking detail page for
                {self.topic} {item[f'{self.topic}']}\n
                topic_prevent:       {topic_prevent}\n
                product_desc:        {product_desc}\n
                error:               {e}
                """)
            self.driver.back()
            # yield item
            return

        item["detail_url"] = self.driver.current_url
        try:
            # Series fields
            title_jp = self.driver.find_element(
                By.XPATH, "//h4[@class='local-fw-normal font-normal text-gray-400']"
            ).text
            title_tw = self.driver.find_element(
                By.XPATH, "//h1[@class='sans-font-semi-bold']"
            ).text
            author_tw = self.driver.find_element(
                By.XPATH, "//div[@class='author flex mb-1']"
            ).text

            # Volume fields
            release_date_tw = self.driver.find_element(
                By.XPATH, "//div[@class='publicDate flex mb-1']"
            ).text
            publisher_tw = self.driver.find_element(
                By.XPATH, "//div[@class='publisher flex mb-1']"
            ).text

            item["title_jp"] = title_jp.strip()
            item["title_tw"] = title_tw.strip()
            item["author_tw"] = author_tw.strip()
            item["release_date_tw"] = release_date_tw.strip()
            item["publisher_tw"] = publisher_tw.strip()
            item["product_desc"] = product_desc.strip()

            self.logger.info(
                f"parse_detail_info(): Successfully parsed series info"
                f"from {self.driver.current_url}"
            )

        except selenium.common.exceptions.NoSuchElementException as e:
            self.logger.error(
                f"parse_detail_info(): Element not found on"
                f"{self.driver.current_url}: {e}"
            )
        except AttributeError as e:
            self.logger.error(
                f"parse_detail_info(): AttributeError parsing series info"
                f"from {self.driver.current_url}: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"parse_detail_info(): Failed to parse series info"
                f"from {self.driver.current_url}, error: {str(e)}",
                exc_info=True,
            )

        finally:
            time.sleep(20)
            # Go back to search results page
            self.driver.back()
            yield item

    def closed(self, reason):
        """See base class."""
        self.logger.info("Closing Selenium driver...")
        if self.driver:
            self.driver.quit()
        self.logger.info("Selenium driver closed.")


class EsliteISBNSpider(EsliteSpider):
    """Spider to scrape Taiwanese book information from eslite.com by book ISBNs."""

    name = "eslite_isbn"

    def __init__(self, *args, **kwargs):
        """See base class."""
        super().__init__(*args, **kwargs)
        self.topic = "isbn_tw"
        self.topic_list = list(
            Volume.objects.filter(
                series__isnull=True, isbn__isnull=False, region="TW"
            ).values_list("isbn", flat=True)
        )
        self.target_info = "//div[@class='product-description-schema']"
        self.logger.info(
            f"EsliteESBNSpider: Loaded {len(self.topic_list)} ISBNs to process."
        )


class EsliteTitleTwSpider(EsliteSpider):
    """Spider to scrape Taiwanese book information from eslite.com by book titles."""

    name = "eslite_title_tw"

    def __init__(self, *args, **kwargs):
        """See base class."""
        super().__init__(*args, **kwargs)
        self.topic = "title_tw"
        if topic_list := kwargs.get("topic_list"):
            self.topic_list = topic_list
            self.last_release_dates = kwargs.get("last_release_dates")
        else:
            self.topic_list = list(
                Series.objects.filter(title_tw__isnull=False).values_list(
                    "title_tw", flat=True
                )
            )
            self.last_release_dates = [
                date.strftime("%Y-%m-%d") if date else None
                for date in Series.objects.filter(title_tw__isnull=False).values_list(
                    "latest_volume_tw__release_date", flat=True
                )
            ]
        self.target_info = "//h1[@class='sans-font-semi-bold']"
        self.logger.info(
            f"EsliteTitleTWSpider: Loaded {len(self.topic_list)}"
            f"Taiwanese titles to process."
        )
