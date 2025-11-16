import os
import django
from itemadapter import ItemAdapter

from comic_scrapers.items import (
    OrphanVolumeItem,
    OrphanMapItem,
    JpComicItem,
    JpVolumeItem
)
from src.comic.models import Publisher, Comic, Volume

class ComicScrapersPipeline:
    def process_item(self, item, spider):
        if isinstance(item, OrphanVolumeItem):
            return self._process_orphan_volume_item(item, spider)
        return item

    def _process_orphan_volume_item(self, item: OrphanVolumeItem, spider):
        """
        Process OrphanVolumeItem by ISBN to create new Volume entry in the database
        """
        # Protect against missing ISBN
        if not item.get('isbn_tw'):
            spider.logger.info(f"OrphanVolumeItem no isbn_tw in: {item['source_url']}")

        # Create Volume entry in Volume Table
        Volume.objects.create(
            isbn_tw=item.get('isbn_tw')
        )

        return item
