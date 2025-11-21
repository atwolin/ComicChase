import os
import re
import django
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from twisted.internet.threads import deferToThread

from comic_scrapers.items import (
    OrphanVolumeItem,
    OrphanMapItem,
    JpComicItem
)
from comic.models import Publisher, Series, Volume

class ComicScrapersPipeline:
    def process_item(self, item, spider):
        # Process data from books.com.tw
        if isinstance(item, OrphanVolumeItem):
            return deferToThread(self._process_orphan_volume_item, item, spider)

        # Process data from eslite.com
        elif isinstance(item, OrphanMapItem):
            return deferToThread(self._process_orphan_map_item, item, spider)

        # Process data from books.or.jp
        elif isinstance(item, JpComicItem):
            return deferToThread(self._process_jp_comic_item, item, spider)
        return item

    def _process_orphan_volume_item(self, item: OrphanVolumeItem, spider):
        """
        Process OrphanVolumeItem by ISBN to create new Volume entry in the database
        """
        spider.logger.info(f"Processing Orphan Volume with ISBN {item.get('isbn_tw')}")
        adapter = ItemAdapter(item)
        isbn_tw = adapter.get('isbn_tw')

        # Protect against missing ISBN
        if not isbn_tw:
            raise DropItem(f"No isbn_tw in OrphanVolumeItem: \n{adapter.items()}\n{'-' * 50}")

        # Create Volume entry in Volume Table
        obj, created = Volume.objects.get_or_create(
            isbn=isbn_tw,
            region='TW'
        )
        if created:
            spider.logger.info(f"Created Orphan Volume with ISBN {isbn_tw}")
        else:
            spider.logger.info(f"Found existing Volume with ISBN {isbn_tw}")

        return item

    def _process_book_title_tw(self, book_title: str):
        """
        Process book_title_tw to extract title and volume number
        Example formats:
            "最後一場閃爍的盛夏 (全)"
            "愚者之夜 9"
            "貓咪好夥伴小圓圓和小八 6 (特裝版)"
            "神速零零壹 2 (完)"
            "藍色時期 16 (首刷限定版)"
            "如果30歲還是處男, 似乎就能成為魔法師 15"
        """
        parts = book_title.split(' ')
        # Series field
        series_name_tw = None
        latest_volume_tw = None
        is_final_volume = False
        # Volume field
        variant = None
        volume_number = None

        # Volume is special edition if "(特裝版)" found
        if parts[-1] in ["(特裝版)", "(首刷限定版)"]:
            variant = parts[-1].strip()
            parts = parts[:-1]
        # Volume is final if "(完)" or "(全)" found
        elif parts[-1] == "(完)":
            is_final_volume = True
            parts = parts[:-1]
        elif parts[-1] == "(全)":
            is_final_volume = True

        # Volume number == 1 if "1" or "(全)" found
        if parts[-1] in ["(全)", "1"]:
            volume_number = 1
        else:
            volume_number = int(parts[-1])

        # Update title_tw
        series_name_tw = ' '.join(parts[:-1]).strip()

        # Update latest_volume_tw if is final volume
        if is_final_volume:
            latest_volume_tw = volume_number

        return series_name_tw, variant, volume_number, is_final_volume, latest_volume_tw

    def _process_orphan_map_item(self, item: OrphanMapItem, spider):
        """
        Process OrphanMapItem to link existing Comics with Volumes in the database
        """
        adapter = ItemAdapter(item)
        isbn_tw = adapter.get('isbn_tw')
        title_jp = adapter.get('title_jp')
        if not title_jp:
            raise DropItem(f"No further information in OrphanMapItem: \n{adapter.items()}\n{'-' * 50}")

        # Process Volume title and volume number
        series_name_tw, variant, volume_number, is_final_volume, latest_volume_tw = self._process_book_title_tw(
            adapter.get('title_tw')
        )
        author_tw = adapter.get('author_tw').rsplit('\n', 1)[-1].strip()

        release_date_tw = adapter.get('release_date_tw').rsplit('：', 1)[-1].strip().replace('/', '-')
        publisher_tw = adapter.get('publisher_tw').rsplit('\n', 1)[-1].strip()

        # Start storing data into database
        # 1. Get or create Publisher
        publisher, created_pub = Publisher.objects.get_or_create(
            name=publisher_tw,
            region='TW'
        )
        if created_pub:
            spider.logger.info(f"Created new Publisher: {publisher}")

        # 2. Get or create Series
        series, created_series = Series.objects.get_or_create(
            title_jp=title_jp,
        )
        if created_series:
            spider.logger.info(f"Created new Series: {series}")
        # Update Series fields
        series.title_tw = series_name_tw
        series.author_tw = author_tw

        # 3. Update Volume
        volume = Volume.objects.filter(isbn_tw=isbn_tw).first()
        if volume:
            volume.series = series
            volume.volume_number = volume_number
            volume.release_date_tw = release_date_tw
            volume.publisher_tw = publisher
            volume.save()
            spider.logger.info(f"Updated Volume: {volume}")
        else:
            spider.logger.warning(f"Volume with ISBN {isbn_tw} not found to update.")

        # Update series's latest_volume_tw if needed
        # if is_final_volume or volume_number > (series.latest_volume_tw or None):
        #     series.latest_volume_tw = volume
        return item

    DATE_JP_REGEX = re.compile(r'[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日')
    REPLACE_WITH_DASH_REGEX = re.compile(r'[年月日]')
    def _get_book_description_jp(self, product_desc: str):
        """
        Process product_desc to extract release date for Japanese comics
        Example formats:
            "発売予定日：2025年12月18日\n"
            "発売日：2025年09月18日\n"
        """
        match = self.DATE_REGEX.search(product_desc)
        if match:
            release_date = match.group(0)
            return self.REPLACE_WITH_DASH_REGEX.sub('-', release_date)
        return None

    VOLUME_NUMBER_JP_REGEX = re.compile(r'[0-9０-９]+')
    def _get_volume_number_jp(self, book_title: str):
        """
        Process title to extract volume number for Japanese comics
        Example formats:
            "廻天のアルバス ７"
            "ブルーピリオド（18）"
            "ブルーピリオド（1）実写映画化記念特装版"
        """
        matches = self.VOLUME_NUMBER_JP_REGEX.findall(book_title)
        if matches:
            volume_number = int(matches[-1].strip())
            title_jp = book_title.replace(matches[-1], '').strip()
            return title_jp, volume_number
        return None


    ISBN_JP_REGEX = re.compile(r'([0-9]{13})')
    def _process_jp_comic_item(self, item: JpComicItem, spider):
        """
        Process JpComicItem to update or create Series and Volume entry in the database
        """
        adapter = ItemAdapter(item)
        detail_url = adapter.get('detail_url')
        if not detail_url:
            raise DropItem(f"No further information in JpComicItem: \n{adapter.items()}\n{'-' * 50}")
        isbn_jp = detail_url.rsplit('/', 1)[-1].strip()
        if self.ISBN_JP_REGEX.match(isbn_jp) is None:
            # One episode, not a full volume
            raise DropItem(f"Invalid ISBN_JP in JpComicItem: \n{adapter.items()}\n{'-' * 50}")

        publisher_jp = adapter.get('publisher_jp').rsplit('出版社：', 1)[-1].strip()

        author_jp = adapter.get('author_jp')[2:]
        author_jp_str = '; '.join(author_jp) if author_jp else ''

        # status_jp = ""
        title_jp, volume_number = self._get_volume_number_jp(adapter.get('title_jp'))
        reslease_date_jp = self._get_book_description_jp(adapter.get('product_desc'))

        # Start storing data into database
        # 1. Get or create Publisher
        publisher, created_pub = Publisher.objects.get_or_create(
            name=publisher_jp,
            region='JP'
        )
        if created_pub:
            spider.logger.info(f"Created new Publisher: {publisher}")

        # 2. Get or create Series
        series, created_series = Series.objects.get_or_create(
            title_jp=title_jp,
            defaults={
                'author_jp': author_jp_str,
                # 'status_jp': status_jp,
            }
        )
        if created_series:
            spider.logger.info(f"Created new Series: {series}")

        # 3. Update Volume
        volume = Volume.objects.get_or_create(
            isbn_jp=isbn_jp,
            defaults={
                'series': series,
                'volume_number': volume_number,
                'release_date_jp': reslease_date_jp,
                'publisher_jp': publisher,
            }
        )
        if volume:
            spider.logger.info(f"Updated Volume: {volume}")
        else:
            spider.logger.warning(f"Volume with ISBN {isbn_jp} not found to update.")

        return item
