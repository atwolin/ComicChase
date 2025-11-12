# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TwComicItem(scrapy.Item):
    # Anchor point field
    isbn_tw = scrapy.Field()
    title_jp = scrapy.Field()

    title_tw = scrapy.Field()
    author_tw = scrapy.Field()


class JpComicItem(scrapy.Item):
    # Anchor point field
    title_jp = scrapy.Field()

    author_jp = scrapy.Field()
    status_jp = scrapy.Field()


class OrphanVolumeItem(scrapy.Item):
    # Anchor point field
    isbn_tw = scrapy.Field()

    volume_number = scrapy.Field()
    release_date_tw = scrapy.Field()
    publisher_tw = scrapy.Field()


class JpVolumeItem(scrapy.Item):
    # Anchor point field
    title_jp = scrapy.Field()

    volume_number = scrapy.Field()
    release_date_jp = scrapy.Field()
    isbn_jp = scrapy.Field()
    publisher_jp = scrapy.Field()
