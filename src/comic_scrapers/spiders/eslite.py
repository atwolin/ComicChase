import time
import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import scrapy
from scrapy.http import HtmlResponse

from comic_scrapers.items import OrphanMapItem
from comic.models import Series, Volume

class EsliteSpider(scrapy.Spider):
    name = "eslite_base"
    allowed_domains = ["eslite.com"]
    start_urls = ["https://www.eslite.com"]

    custom_settings = {
        'TWISTED_REACTOR': 'twisted.internet.selectreactor.SelectReactor',
    }

    def __init__(self, *args, **kwargs):
        """
        Change default settings for Selenium
        """
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        self.topic = ""
        self.topic_list = []
        self.target_info = ""

    def start_requests(self):
        """
        Passing URL via meta to avoid linting errors
        """
        url = self.start_urls[0]
        # Load the homepage without waiting for a specific element
        self.driver.get(url)
        time.sleep(2)

        self.logger.debug(f"start_requests(): Loaded homepage {url}")

        response = HtmlResponse(
            url=self.driver.current_url, body=self.driver.page_source,
            encoding='utf-8', request=scrapy.Request(url=url))
        yield from self.parse(response)

    def parse(self, response: HtmlResponse):
        """
        Generate search results URL for each topic item and yield request to parse detail page link
        """
        self.logger.debug(f"parse(): Start parsing from {response.url}")

        input_xpath = "//input[@name='query']"

        for i, topic_item in enumerate(self.topic_list):
            # TESTING: Stop after processing first 3 items
            if i == 2:
                break
            self.logger.debug(f"parse(): Processing {self.topic} {topic_item} ({i + 1}/{len(self.topic_list)})")

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

            yield from self.parse_search_results(topic_item)
            time.sleep(2)

            self.logger.debug(f"parse(): Completed processing item {topic_item} ({i + 1}/{len(self.topic_list)})")

    def parse_search_results(self, topic_item, prev_url=None):
        """
        Obtain book URLs from the search results URL and
        find the only matching URL that contains the targeted topic item
        """
        self.logger.debug(f"parse_search_results(): Parsing search results from {self.driver.current_url}")
        if prev_url == self.driver.current_url:
            self.logger.info("No more pages to process")
            return

        time.sleep(2)
        # Only click category filter on the first page (when prev_url is None)
        if prev_url is None:
            try:
                category_tw = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@title='中文書']")))
                category_tw.click()
                time.sleep(2)
            except selenium.common.exceptions.TimeoutException as e:
                self.logger.error(f"parse_search_results(): Timeout while applying category filter for {self.topic} {topic_item}: {e}")

        # Get book detail links
        links_xpath = "//a[@class='item-image-link']"
        try:
            links = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, links_xpath)))
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(f"parse_search_results(): Timeout while locating book links for {self.topic} {topic_item}: {e}")
            # Create and yield empty item to track failed search
            item = OrphanMapItem()
            item[f'{self.topic}'] = topic_item
            item['search_url'] = self.driver.current_url
            yield item
            return
        self.logger.debug(f"parse_search_results(): Found {len(links)} book links on the search results page.")

        # Parse each result link
        n = len(links)
        for i in range(n):
            # TESTING: Stop after processing first 3 links
            if i == 2:
                break
            self.logger.debug(f"parse_search_results(): Processing link {i + 1}/{n}")

            # Create a new item for each link
            item = OrphanMapItem()
            item[f'{self.topic}'] = topic_item
            item['search_url'] = self.driver.current_url

            yield from self.parse_detail_info(links[i], item)
            time.sleep(2)

            self.logger.debug(f"parse_search_results(): Completed processing link {i + 1}/{n}")
            # Refresh links list after navigating back to avoid stale element reference
            links = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, links_xpath)))
            time.sleep(2)

        # Go to next page
        # TESTING: Stop after first page
        return

        prev_url = self.driver.current_url
        next_button_xpath = "//div[@class='page-number']/div[@data-gid='pagination-next']"
        try:
            next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
            next_button.click()
            time.sleep(2)
            yield from self.parse_search_results(topic_item, prev_url)
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(f"parse_search_results(): Timeout because no next button found for {self.topic} {topic_item}: {e}")

    def parse_detail_info(self, link, item: OrphanMapItem):
        """
        Extract series and volume information from the book URL
        """
        self.logger.debug(f"parse_detail_info(): Parsing series info from {self.driver.current_url}")

        product_desc = None
        topic_prevent = None
        try:
            link.click()
            topic_prevent_xpath = self.target_info
            topic_prevent_webelement = self.wait.until(EC.presence_of_element_located((By.XPATH, topic_prevent_xpath)))
            topic_prevent = topic_prevent_webelement.get_attribute('innerHTML')
            category_xpath = "//a[@title='動漫畫／圖文']"
            category_webelement = self.wait.until(EC.presence_of_element_located((By.XPATH, category_xpath)))
            product_desc_xpath = "//div[@class='product-description-schema']"
            product_desc_webelement = self.wait.until(EC.presence_of_element_located((By.XPATH, product_desc_xpath)))
            product_desc = product_desc_webelement.get_attribute('innerHTML')
            if not item[f'{self.topic}'] in topic_prevent or 'JP-eコード' in product_desc:
                self.driver.back()
                yield item
                return
        except selenium.common.exceptions.TimeoutException as e:
            self.logger.error(f"""
                parse_detail_info(): Timeout while checking detail page for {self.topic} {item[f'{self.topic}']}\n
                topic_prevent:       {topic_prevent}\n
                product_desc:        {product_desc}\n
                error:               {e}
                """)
            self.driver.back()
            # yield item
            return

        item['detail_url'] = self.driver.current_url
        try:
            # Series fields
            title_jp = self.driver.find_element(By.XPATH, "//h4[@class='local-fw-normal font-normal text-gray-400']").text
            title_tw = self.driver.find_element(By.XPATH, "//h1[@class='sans-font-semi-bold']").text
            author_tw = self.driver.find_element(By.XPATH, "//div[@class='author flex mb-1']").text

            # Volume fields
            release_date_tw = self.driver.find_element(By.XPATH, "//div[@class='publicDate flex mb-1']").text
            publisher_tw = self.driver.find_element(By.XPATH, "//div[@class='publisher flex mb-1']").text

            item['title_jp'] = title_jp.strip()
            item['title_tw'] = title_tw.strip()
            item['author_tw'] = author_tw.strip()
            item['release_date_tw'] = release_date_tw.strip()
            item['publisher_tw'] = publisher_tw.strip()
            item['product_desc'] = product_desc.strip()

            self.logger.info(f"parse_detail_info(): Successfully parsed series info from {self.driver.current_url}")

        except AttributeError as e:
            self.logger.error(f"parse_detail_info(): Error parsing series info from {self.driver.current_url}: {e}")

        finally:
            time.sleep(20)
            # Go back to search results page
            self.driver.back()
            yield item

    def closed(self, resaon):
        """
        Close the Selenium driver when spider is closed
        """
        self.logger.info("Closing Selenium driver...")
        if self.driver:
            self.driver.quit()
        self.logger.info("Selenium driver closed.")


class EsliteISBNSpider(EsliteSpider):
    name = "eslite_isbn"

    def __init__(self, *args, **kwargs):
        """
        Change default settings for Selenium
        """
        super().__init__(*args, **kwargs)
        self.topic = "isbn_tw"
        self.topic_list = list(Volume.objects
                         .filter(series__isnull=True, isbn__isnull=False, region='TW')
                         .values_list('isbn', flat=True))
        self.target_info = "//div[@class='product-description-schema']"
        self.logger.info(f"EsliteESBNSpider: Loaded {len(self.topic_list)} ISBNs to process.")


class EsliteTitleTwSpider(EsliteSpider):
    name = "eslite_title_tw"

    def __init__(self, *args, **kwargs):
        """
        Change default settings for Selenium
        """
        super().__init__(*args, **kwargs)
        self.topic = "title_tw"
        # self.topic_list = list(Series.objects
        #                     .filter(isnull=True, title_tw__isnull=False)
        #                     .values_list('title_tw', flat=True))
        # self.topic_list = ["迴天的阿爾帕斯"]
        self.topic_list = ["藍色時期"]
        self.target_info = "//h1[@class='sans-font-semi-bold']"
        self.logger.info(f"EsliteTitleTWSpider: Loaded {len(self.topic_list)} Taiwanese titles to process.")
