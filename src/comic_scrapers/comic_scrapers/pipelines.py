import os
import django
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from asgiref.sync import sync_to_async

from comic_scrapers.items import (
    OrphanVolumeItem,
    OrphanMapItem,
    JpComicItem,
    JpVolumeItem
)
from comic.models import Publisher, Comic, Volume

class ComicScrapersPipeline:
    async def process_item(self, item, spider):
        # Process data from books.com.tw
        if isinstance(item, OrphanVolumeItem):
            return await self._process_orphan_volume_item(item, spider)
        return item

    @sync_to_async
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
            isbn_tw=isbn_tw
        )
        if created:
            spider.logger.info(f"Created Orphan Volume with ISBN {isbn_tw}")
        else:
            spider.logger.info(f"Found existing Volume with ISBN {isbn_tw}")

        return item
