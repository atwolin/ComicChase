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

        # Protect against missing ISBN
        if not adapter.get('isbn_tw'):
            raise DropItem("Missing isbn_tw in OrphanVolumeItem")
            return

        # Create Volume entry in Volume Table
        Volume.objects.create(
            isbn_tw=adapter.get('isbn_tw')
        )
        spider.logger.info(f"Created Orphan Volume with ISBN {adapter.get('isbn_tw')}")

        return item
