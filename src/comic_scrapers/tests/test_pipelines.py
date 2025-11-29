"""Unit tests for the pipeline processing methods."""

import unittest
from unittest.mock import MagicMock, patch

from scrapy.exceptions import DropItem

from comic_scrapers.items import JpComicItem, OrphanMapItem, OrphanVolumeItem
from comic_scrapers.pipelines import ComicScrapersPipeline


class TestGetBookTitleTw(unittest.TestCase):
    """Test cases for the _get_book_title_tw() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ComicScrapersPipeline()

    def test_get_book_title_tw_with_volume_number(self):
        """Test parsing title with volume number."""
        book_title = "藍色時期 16"

        series_name_tw, variant, volume_number, is_final, latest_volume = (
            self.pipeline._get_book_title_tw(book_title)
        )

        self.assertEqual(series_name_tw, "藍色時期")
        self.assertIsNone(variant)
        self.assertEqual(volume_number, 16)
        self.assertFalse(is_final)
        self.assertIsNone(latest_volume)

    def test_get_book_title_tw_with_special_edition(self):
        """Test parsing title with special edition marker."""
        book_title = "貓咪好夥伴小圓圓和小八 6 (特裝版)"

        series_name_tw, variant, volume_number, is_final, latest_volume = (
            self.pipeline._get_book_title_tw(book_title)
        )

        self.assertEqual(series_name_tw, "貓咪好夥伴小圓圓和小八")
        self.assertEqual(variant, "特裝版")
        self.assertEqual(volume_number, 6)
        self.assertFalse(is_final)
        self.assertIsNone(latest_volume)

    def test_get_book_title_tw_with_final_volume_marker(self):
        """Test parsing title with final volume marker."""
        book_title = "神速零零壹 2 (完)"

        series_name_tw, variant, volume_number, is_final, latest_volume = (
            self.pipeline._get_book_title_tw(book_title)
        )

        self.assertEqual(series_name_tw, "神速零零壹")
        self.assertIsNone(variant)
        self.assertEqual(volume_number, 2)
        self.assertTrue(is_final)
        self.assertEqual(latest_volume, 2)


class TestGetBookReleaseDateJp(unittest.TestCase):
    """Test cases for the _get_book_release_date_jp() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ComicScrapersPipeline()

    def test_get_book_release_date_jp_valid_format(self):
        """Test parsing valid date format."""
        product_desc = "発売予定日：2025年12月18日\n"

        result = self.pipeline._get_book_release_date_jp(product_desc)

        self.assertEqual(result, "2025-12-18")

    def test_get_book_release_date_jp_single_digit_padding(self):
        """Test padding single digit month and day with leading zeros."""
        product_desc = "発売日：2018年1月6日\n"

        result = self.pipeline._get_book_release_date_jp(product_desc)

        self.assertEqual(result, "2018-01-06")

    def test_get_book_release_date_jp_invalid_format(self):
        """Test returning None for invalid date format."""
        product_desc = "Some random text without date"

        result = self.pipeline._get_book_release_date_jp(product_desc)

        self.assertIsNone(result)


class TestGetBookTitleJp(unittest.TestCase):
    """Test cases for the _get_book_title_jp() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ComicScrapersPipeline()

    def test_get_book_title_jp_with_arabic_numeral(self):
        """Test parsing title with Arabic numeral volume number."""
        book_title = "廻天のアルバス ７"
        series_name = "廻天のアルバス"

        variant, volume_number = self.pipeline._get_book_title_jp(
            book_title, series_name
        )

        self.assertEqual(variant, "")
        self.assertEqual(volume_number, 7)

    def test_get_book_title_jp_with_parentheses(self):
        """Test parsing title with parentheses around volume number."""
        book_title = "ブルーピリオド（18）"
        series_name = "ブルーピリオド"

        variant, volume_number = self.pipeline._get_book_title_jp(
            book_title, series_name
        )

        self.assertEqual(variant, "")
        self.assertEqual(volume_number, 18)

    def test_get_book_title_jp_with_variant(self):
        """Test parsing title with variant information."""
        book_title = "ブルーピリオド（1）実写映画化記念特装版"
        series_name = "ブルーピリオド"

        variant, volume_number = self.pipeline._get_book_title_jp(
            book_title, series_name
        )

        self.assertEqual(variant, "実写映画化記念特装版")
        self.assertEqual(volume_number, 1)


class TestProcessOrphanVolumeItem(unittest.TestCase):
    """Test cases for the _process_orphan_volume_item() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ComicScrapersPipeline()
        self.spider = MagicMock()

    @patch("comic_scrapers.pipelines.Volume")
    def test_process_orphan_volume_item_creates_new_volume(self, mock_volume):
        """Test successful creation of new Volume with valid ISBN."""
        item = OrphanVolumeItem()
        item["isbn_tw"] = "9786264364843"
        item["source_url"] = "https://example.com"

        mock_volume.objects.get_or_create.return_value = (MagicMock(), True)

        result = self.pipeline._process_orphan_volume_item(item, self.spider)

        mock_volume.objects.get_or_create.assert_called_once_with(
            isbn="9786264364843",
            defaults={
                "region": "TW",
                "variant": "",
            },
        )
        self.assertEqual(result, item)

    @patch("comic_scrapers.pipelines.Volume")
    def test_process_orphan_volume_item_raises_drop_item_on_missing_isbn(
        self, mock_volume
    ):
        """Test raising DropItem when isbn_tw is missing."""
        item = OrphanVolumeItem()
        item["isbn_tw"] = None

        with self.assertRaises(DropItem) as context:
            self.pipeline._process_orphan_volume_item(item, self.spider)

        self.assertIn("No isbn_tw", str(context.exception))

    @patch("comic_scrapers.pipelines.Volume")
    def test_process_orphan_volume_item_handles_existing_volume(self, mock_volume):
        """Test handling of existing Volume (get_or_create returns existing)."""
        item = OrphanVolumeItem()
        item["isbn_tw"] = "9786264364843"

        mock_volume.objects.get_or_create.return_value = (MagicMock(), False)

        result = self.pipeline._process_orphan_volume_item(item, self.spider)

        self.assertEqual(result, item)
        self.spider.logger.warning.assert_called()


class TestProcessOrphanMapItem(unittest.TestCase):
    """Test cases for the _process_orphan_map_item() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ComicScrapersPipeline()
        self.spider = MagicMock()

    @patch("comic_scrapers.pipelines.Volume")
    @patch("comic_scrapers.pipelines.Series")
    @patch("comic_scrapers.pipelines.Publisher")
    def test_process_orphan_map_item_creates_publisher_series_updates_volume(
        self, mock_publisher, mock_series, mock_volume
    ):
        """Test processing with creating Publisher, Series, & updating Volume."""
        item = OrphanMapItem()
        item["isbn_tw"] = "9786260243098"
        item["title_jp"] = "ブルーピリオド"
        item["title_tw"] = "藍色時期 16 (首刷限定版)"
        item["author_tw"] = "作\n者：\n山口飛翔"
        item["release_date_tw"] = "出\n版\n日\n期：\n2025/11/27"
        item["publisher_tw"] = "出\n版\n社：\n東立出版社有限公司"

        mock_pub_obj = MagicMock()
        mock_publisher.objects.get_or_create.return_value = (mock_pub_obj, True)

        mock_series_obj = MagicMock()
        mock_series_obj.latest_volume_tw = None
        mock_series.objects.get_or_create.return_value = (mock_series_obj, True)

        mock_volume_obj = MagicMock()
        mock_volume_obj.release_date = None
        mock_volume.objects.filter.return_value.first.return_value = mock_volume_obj

        result = self.pipeline._process_orphan_map_item(item, self.spider)

        mock_publisher.objects.get_or_create.assert_called_once_with(
            name="東立出版社有限公司", region="TW"
        )
        mock_series.objects.get_or_create.assert_called_once_with(
            title_jp="ブルーピリオド"
        )
        self.assertEqual(mock_series_obj.title_tw, "藍色時期")
        self.assertEqual(mock_series_obj.author_tw, "山口飛翔")
        self.assertEqual(result, item)

    def test_process_orphan_map_item_raises_drop_item_on_missing_title_jp(self):
        """Test raising DropItem when title_jp is missing."""
        item = OrphanMapItem()
        item["title_jp"] = None

        with self.assertRaises(DropItem) as context:
            self.pipeline._process_orphan_map_item(item, self.spider)

        self.assertIn("No further information", str(context.exception))

    @patch("comic_scrapers.pipelines.Volume")
    @patch("comic_scrapers.pipelines.Series")
    @patch("comic_scrapers.pipelines.Publisher")
    def test_process_orphan_map_item_warns_when_volume_not_found(
        self, mock_publisher, mock_series, mock_volume
    ):
        """Test warning when Volume with ISBN not found."""
        item = OrphanMapItem()
        item["isbn_tw"] = "9786264306775"
        item["title_jp"] = "ラストサマースパークル"
        item["title_tw"] = "最後一場閃爍的盛夏 (全)"
        item["author_tw"] = "作\n者：\n内海ロング"
        item["release_date_tw"] = "出\n版\n日\n期：\n2025/11/18"
        item["publisher_tw"] = "出\n版\n社：\n長鴻出版社股份有限公司"

        mock_publisher.objects.get_or_create.return_value = (MagicMock(), True)
        mock_series_obj = MagicMock()
        mock_series_obj.latest_volume_tw = None
        mock_series.objects.get_or_create.return_value = (mock_series_obj, True)
        mock_volume.objects.filter.return_value.first.return_value = None

        result = self.pipeline._process_orphan_map_item(item, self.spider)

        self.spider.logger.warning.assert_called()
        self.assertEqual(result, item)


class TestProcessJpComicItem(unittest.TestCase):
    """Test cases for the _process_jp_comic_item() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ComicScrapersPipeline()
        self.spider = MagicMock()

    @patch("comic_scrapers.pipelines.Volume")
    @patch("comic_scrapers.pipelines.Series")
    @patch("comic_scrapers.pipelines.Publisher")
    def test_process_jp_comic_item_creates_all_entities(
        self, mock_publisher, mock_series, mock_volume
    ):
        """Test successful processing creating Publisher, Series, and Volume."""
        item = JpComicItem()
        item["series_name"] = "廻天のアルバス"
        item["title_jp"] = "廻天のアルバス ７"
        item["author_jp"] = [
            "",
            "少年サンデーコミックス",
            "原案：牧 彰久",
            "絵：箭坪 幹",
        ]
        item["publisher_jp"] = "出版社：小学館"
        item["detail_url"] = "https://www.books.or.jp/book-details/9784098543724"
        item["product_desc"] = (
            '<p class="text-body text-color">ISBN：9784098543724<br>'
            "雑誌コード：5854372<br>出版社：小学館<br>判型：新書<br>"
            "ページ数：192ページ<br>定価：540円（本体）<br>"
            "発行年月日：2025年12月23日<br>発売予定日：2025年12月18日"
            '<span class="readonly">。</span></p>'
        )

        mock_pub_obj = MagicMock()
        mock_publisher.objects.get_or_create.return_value = (mock_pub_obj, True)

        mock_series_obj = MagicMock()
        mock_series_obj.latest_volume_jp = None
        mock_series.objects.get_or_create.return_value = (mock_series_obj, True)

        mock_volume_obj = MagicMock()
        mock_volume.objects.get_or_create.return_value = (mock_volume_obj, True)

        result = self.pipeline._process_jp_comic_item(item, self.spider)

        mock_publisher.objects.get_or_create.assert_called_once_with(
            name="小学館", region="JP"
        )
        mock_series.objects.get_or_create.assert_called_once_with(
            title_jp="廻天のアルバス"
        )
        self.assertEqual(mock_series_obj.author_jp, "絵：箭坪 幹")
        self.assertEqual(result, item)

    def test_process_jp_comic_item_raises_drop_item_on_missing_detail_url(self):
        """Test raising DropItem when detail_url is missing."""
        item = JpComicItem()
        item["detail_url"] = None
        item["series_name"] = "廻天のアルバス"

        with self.assertRaises(DropItem) as context:
            self.pipeline._process_jp_comic_item(item, self.spider)

        self.assertIn("No further information", str(context.exception))

    def test_process_jp_comic_item_raises_drop_item_on_invalid_isbn(self):
        """Test raising DropItem when ISBN is invalid (not 13 digits)."""
        item = JpComicItem()
        item["series_name"] = "廻天のアルバス"
        item["title_jp"] = "廻天のアルバス ７"
        item["detail_url"] = "https://www.books.or.jp/invalid_isbn"

        with self.assertRaises(DropItem) as context:
            self.pipeline._process_jp_comic_item(item, self.spider)

        self.assertIn("Invalid ISBN_JP", str(context.exception))


if __name__ == "__main__":
    unittest.main()
