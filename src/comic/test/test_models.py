from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from comic.models import Publisher, Series, Volume

class PublisherModelTests(TestCase):
    def test_create_publishers_for_both_regions(self):
        """測試建立出版社"""
        jp = Publisher.objects.create(name="講談社", region=Publisher.Region.JAPAN)
        tw = Publisher.objects.create(name="東立", region=Publisher.Region.TAIWAN)

        self.assertEqual(Publisher.objects.count(), 2)
        self.assertEqual(jp.region, Publisher.Region.JAPAN)
        self.assertEqual(tw.region, Publisher.Region.TAIWAN)

    def test_str_returns_name_and_region(self):
        """測試 __str__ 方法正確顯示名稱和地區"""
        publisher = Publisher.objects.create(name="角川", region=Publisher.Region.JAPAN)
        self.assertIn("角川", str(publisher))
        self.assertIn("Japan", str(publisher))

    def test_name_uniqueness_enforced(self):
        """測試 name 的唯一性約束"""
        Publisher.objects.create(name="集英社", region=Publisher.Region.JAPAN)
        with self.assertRaises(IntegrityError):
            Publisher.objects.create(name="集英社", region=Publisher.Region.TAIWAN)

class SeriesModelTests(TestCase):
    def setUp(self):
        self.publisher = Publisher.objects.create(name="講談社", region=Publisher.Region.JAPAN)

    def test_create_series_with_multilingual_fields(self):
        """測試建立系列漫畫"""
        series = Series.objects.create(
            title_jp="進撃の巨人",
            title_tw="進擊的巨人",
            author_jp="諫山創",
            author_tw="諫山創",
            status_jp=Series.JapanStatus.COMPLETED,
        )
        self.assertEqual(series.title_tw, "進擊的巨人")
        self.assertEqual(series.author_tw, "諫山創")
        self.assertEqual(series.status_jp, Series.JapanStatus.COMPLETED)

    def test_status_choices_validation(self):
        """測試作品狀態選項驗證"""
        with self.assertRaises(ValidationError):
            series = Series(
                title_jp="錯誤狀態作品",
                author_jp="Unknown",
                status_jp="invalid", # 無效的狀態
            )
            series.full_clean()

    def test_latest_volume_relations(self):
        """測試 latest_volume 的外鍵關聯"""
        series = Series.objects.create(
            title_jp="ブルーピリオド",
            title_tw="藍色時期",
            author_jp="山口つばさ",
        )
        latest_jp = Volume.objects.create(
            series=series,
            publisher=self.publisher,
            region=Volume.Region.JAPAN,
            volume_number=17,
            isbn="9781234567890",
        )
        latest_tw = Volume.objects.create(
            series=series,
            publisher=self.publisher,
            region=Volume.Region.TAIWAN,
            volume_number=15,
            isbn="9789876543210",
        )
        series.latest_volume_jp = latest_jp
        series.latest_volume_tw = latest_tw
        series.save()

        refreshed = Series.objects.get(pk=series.pk)
        self.assertEqual(refreshed.latest_volume_jp, latest_jp)
        self.assertEqual(refreshed.latest_volume_tw, latest_tw)

    def test_str_prefers_traditional_chinese_title(self):
        """測試 __str__ 方法優先顯示中文標題"""
        series = Series.objects.create(
            title_jp="怪獣8号",
            title_tw="怪獸8號",
            author_jp="松本直也",
        )
        self.assertEqual(str(series), "怪獸8號")

class VolumeModelTests(TestCase):
    def setUp(self):
        self.publisher_jp = Publisher.objects.create(name="講談社", region=Publisher.Region.JAPAN)
        self.series = Series.objects.create(title_jp="チェンソーマン", author_jp="藤本タツキ")

    def test_create_volume_for_both_regions(self):
        """測試建立不同地區(JP/TW)的單行本"""
        jp_volume = Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.JAPAN,
            volume_number=13,
            isbn="9781234567000",
        )
        tw_volume = Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.TAIWAN,
            volume_number=13,
            isbn="9781234567999",
        )

        self.assertEqual(jp_volume.region, Volume.Region.JAPAN)
        self.assertEqual(tw_volume.region, Volume.Region.TAIWAN)

    def test_create_volume_variant(self):
        """測試版本備註的功能"""
        special_volume = Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.TAIWAN,
            volume_number=13,
            variant="特裝版",
            isbn="9781234567888",
        )

        self.assertEqual(special_volume.variant, "特裝版")

    def test_unique_volume_variant_constraint(self):
        """測試 UniqueConstraint (unique_volume_variant)"""
        # 建立第一本
        Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.JAPAN,
            volume_number=1,
            variant="",
            isbn="9781111111111",
        )
        # 嘗試建立重複的，除 ISBN 不同
        with self.assertRaises(IntegrityError):
            Volume.objects.create(
                series=self.series,
                publisher=self.publisher_jp,
                region=Volume.Region.JAPAN,
                volume_number=1,
                variant="",
                isbn="9782222222222", 
            )

    def test_isbn_uniqueness(self):
        """測試 ISBN 的唯一性"""
        Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.JAPAN,
            volume_number=5,
            isbn="9783333333333",
        )
        with self.assertRaises(IntegrityError):
            Volume.objects.create(
                series=self.series,
                publisher=self.publisher_jp,
                region=Volume.Region.TAIWAN,
                volume_number=5,
                isbn="9783333333333", # 重複的 ISBN
            )

    def test_str_representation(self):
        """測試 __str__ 方法的顯示格式"""
        volume = Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.JAPAN,
            volume_number=2,
            variant="首刷限定",
            isbn="9784444444444",
        )
        result = str(volume)
        self.assertIn("Japan", result)
        self.assertIn("Vol. 2", result)
        self.assertIn("首刷限定", result)

    def test_variant_defaults_to_empty_string(self):
        """測試 variant 預設為空字串"""
        volume = Volume.objects.create(
            series=self.series,
            publisher=self.publisher_jp,
            region=Volume.Region.JAPAN,
            volume_number=7,
            isbn="9785555555555",
        )
        self.assertEqual(volume.variant, "")
