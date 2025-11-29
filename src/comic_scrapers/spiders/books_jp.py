import re
import time

import scrapy
import selenium
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comic.models import Series
from comic_scrapers.items import JpComicItem


class BooksJpSpider(scrapy.Spider):
    """Spider to scrape Japanese book information from books.or.jp site.

    This spider obtain book urls and extracts volume information
    such as author, release date, and publisher.
    """

    name = "books_jp"
    allowed_domains = ["books.or.jp"]
    start_urls = ["https://www.books.or.jp/"]

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

        Because the date format in books.or.jp is in Japanese,
        we use a regex to extract the date components and reformat them to YYYY-MM-DD.
        Example formats:
            "2025年12月18日\n" -> "2025-12-18"
            "2018年12月06日\n" -> "2018-12-06"

        Args:
            product_desc (str): The product description string
            containing the release date.

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
            JpComicItem: Item containing the extracted comic information.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found.
            NoSuchElementException: If expected HTML elements are not found.
            Exception: If any error occurs during parsing.
        """
        self.logger.debug(f"parse(): Start parsing from {response.url}")

        input_xpath = "//input[@id='searchforbooks_title']"
        search_buttom_xpath = "//button[@class='searchforbooks_search_button']"

        for i, topic_item in enumerate(self.topic_list):
            # # TESTING: Stop after processing first 3 items
            # if i == 2:
            #     break
            # # END TESTING

            try:
                self.logger.debug(
                    f"parse(): Processing {self.topic}: {topic_item}"
                    f" ({i + 1}/{len(self.topic_list)})"
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

                # Click the search button
                search_button = self.driver.find_element(By.XPATH, search_buttom_xpath)
                search_button.click()

                # Wait for search results page to load before parsing
                time.sleep(3)

                yield from self.parse_search_results(topic_item, i)
                time.sleep(2)

                self.logger.debug(
                    f"parse(): Completed processing {topic_item}"
                    f" ({i + 1}/{len(self.topic_list)})"
                )

            except selenium.common.exceptions.TimeoutException as e:
                self.logger.error(
                    f"parse(): Timeout while processing"
                    f" {self.topic} {topic_item}: {e}"
                )
            except selenium.common.exceptions.NoSuchElementException as e:
                self.logger.error(
                    f"parse(): Element not found while processing"
                    f" {self.topic} {topic_item}: {e}"
                )
            except Exception as e:
                self.logger.error(
                    f"parse(): Failed to process"
                    f" {self.topic} {topic_item},"
                    f" error: {str(e)}",
                    exc_info=True,
                )

    def parse_search_results(self, topic_item: str, series_index: int):
        """Parse the search results page to extract book detail urls.

        Parse each search results page to find book detail urls and their release dates.
        If a book's release date is not newer than the last recorded release date,
        it will be skipped.

        Args:
            topic_item (str): The current topic item being processed.
            series_index (int): The index of the current series in topic_list.

        Yields:
            JpComicItem: Item containing the extracted comic information.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found
                              or no more pages are found.
        """
        self.logger.debug(
            f"parse_search_results(): Parsing search results from"
            f"{self.driver.current_url}"
        )

        time.sleep(2)

        # Get book detail links
        links_xpath = "//a[@class='result_list_button']"
        links = None
        volume_release_date_xpath = (
            "//div[" "@class='result_list_discription_publishdate']"
        )
        volume_release_dates = None
        try:
            links = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, links_xpath))
            )
            volume_release_dates = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, volume_release_date_xpath)
                )
            )
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(
                f"parse_search_results(): "
                f"Timeout while locating book links for "
                f"{self.topic} {topic_item}: {e}"
            )
            # Create and yield empty item to track failed search
            item = JpComicItem()
            item[f"{self.topic}"] = topic_item
            yield item
            return
        self.logger.debug(
            f"parse_search_results(): Found {len(links)}"
            "book links on the search results page."
        )

        # Parse each result link
        n = len(links)
        for i in range(n):
            # # TESTING: Stop after processing first 3 links
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
                        "parse_search_results(): Skipping link"
                        f"{i + 1}/{n} - already have this volume\n"
                        f"current_release_date: {current_release_date},"
                        f" last_release_date: {self.last_release_dates[series_index]}"
                    )
                    continue

            self.logger.debug(f"parse_search_results(): Processing link {i + 1}/{n}")

            # Create a new item for each link
            item = JpComicItem()
            item[f"{self.topic}"] = topic_item

            yield from self.parse_detail_info(links[i], item)
            time.sleep(2)

            self.logger.debug(
                "parse_search_results(): Completed processing link" f"{i + 1}/{n}"
            )
            # Refresh links list after navigating back to avoid stale element reference
            links = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, links_xpath))
            )
            time.sleep(2)

        # # Go to next page
        # # TESTING: Stop after first page
        # return
        # # END TESTING

        next_button_xpath = "//button[@aria-label='1ページ後に進む']"
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, next_button_xpath))
            )
            next_button.click()
            time.sleep(2)
            self.logger.debug(
                "parse_search_results(): Navigated to next page of"
                f"search results for {self.topic} {topic_item}"
            )
            yield from self.parse_search_results(topic_item, series_index)
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(
                f"parse_search_results(): Timeout because"
                "no next button found for"
                f" {self.topic} {topic_item}: {e}"
            )

    def parse_detail_info(self, link: str, item: JpComicItem):
        """Extract series and volume information from the book URL.

        Retrieves the book detail page and extracts series author, book title,
        publisher, and product description, which including ISBN and release date.

        Args:
            url (str): The URL of the book detail page.
            item (JpComicItem): Item containing the extracted comic information.

        Yields:
            JpComicItem: Item containing the extracted comic information.

        Raises:
            TimeoutException: If a timeout occurs because elements cannot be found.
            NoSuchElementException: If expected HTML elements are not found.
            AttributeError: If expected HTML elements for book information
                            are not found.
            Exception: If any error occurs during parsing.
        """
        self.logger.debug(
            f"parse_detail_info(): Parsing comic info from" f"{self.driver.current_url}"
        )

        product_desc = None
        topic_prevent = None
        try:
            link.click()
            # Check if the topic is present in the detail page or if it's a e-book
            topic_prevent_xpath = self.target_info
            topic_prevent_webelement = self.wait.until(
                EC.presence_of_element_located((By.XPATH, topic_prevent_xpath))
            )
            topic_prevent = topic_prevent_webelement.get_attribute("innerHTML")
            product_desc_xpath = "//div[@class='otherdata']"
            product_desc_webelement = self.wait.until(
                EC.presence_of_element_located((By.XPATH, product_desc_xpath))
            )
            product_desc = product_desc_webelement.get_attribute("innerHTML")
            if (
                item[f"{self.topic}"] not in topic_prevent
                or "JP-eコード" in product_desc
            ):
                self.driver.back()
                yield item
                return
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(f"""
                parse_detail_info(): Timeout while checking detail page for
                {self.topic} {item[f'{self.topic}']}, \n
                topic_prevent:       {topic_prevent}, \n
                product_desc:        {product_desc}, \n
                error:               {e}
                """)
            self.driver.back()
            yield item
            return

        item["detail_url"] = self.driver.current_url
        try:
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
            item["product_desc"] = product_desc.strip()

            self.logger.info(
                f"parse_detail_info(): Successfully parsed comic info from"
                f"{self.driver.current_url}"
            )

        except selenium.common.exceptions.NoSuchElementException as e:
            self.logger.error(
                f"parse_detail_info(): Element not found on"
                f"{self.driver.current_url}: {e}"
            )
        except AttributeError as e:
            self.logger.error(
                f"parse_detail_info(): AttributeError parsing comic info"
                f"from {self.driver.current_url}: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"parse_detail_info(): Failed to parse comic info"
                f"from {self.driver.current_url}, error: {str(e)}",
                exc_info=True,
            )

        finally:
            time.sleep(20)
            # Go back to search results page
            self.driver.back()
            yield item

    def closed(self, resaon):
        """See base class."""
        self.logger.info("Closing Selenium driver...")
        if hasattr(self, "driver") and self.driver:
            self.driver.quit()
        self.logger.info("Selenium driver closed.")


class BooksJpTitleTwSpider(BooksJpSpider):
    """Spider to scrape Japanese book information from books.or.jp site
    by Japanese series name."""

    name = "booksjp_title"

    def __init__(self, *args, **kwargs):
        """See base class."""
        super().__init__(*args, **kwargs)
        self.topic = "series_name"
        self.topic_list = list(
            Series.objects.filter(title_jp__isnull=False, author_jp=None).values_list(
                "title_jp", flat=True
            )
        )
        # self.topic_list = ["廻天のアルバス", "ブルーピリオド"]
        # self.topic_list = ["ブルーピリオド"]
        # self.last_release_dates = [datetime.now().strftime("%Y-%m-%d")]
        self.target_info = "//span[@class='bookdetail_title_text']"
        self.last_release_dates = [
            date.strftime("%Y-%m-%d") if date else None
            for date in Series.objects.filter(
                title_jp__isnull=False, author_jp=None
            ).values_list("last_release_date", flat=True)
        ]
        self.logger.info(
            f"BooksJpTitleTwSpider: Loaded {len(self.topic_list)}"
            "Japanese titles to process."
        )
