import scrapy


class OrphanVolumeItem(scrapy.Item):
    """
    Item for volumes that do not have an associated comic yet

    Fields:
        isbn_tw: The ISBN of the volume in Taiwan
        volume_number: The volume number of the volume
        release_date_tw: The release date of the volume in Taiwan
        publisher_tw: The publisher of the volume in Taiwan
    """
    # Anchor point field
    isbn_tw = scrapy.Field()

    # volume_number = scrapy.Field()
    # release_date_tw = scrapy.Field()
    # publisher_tw = scrapy.Field()
    # source_url = scrapy.Field()


class OrphanMapItem(scrapy.Item):
    """
    Item for mapping volume to comic when new volume found without associated comic

    Fields:
        isbn_tw: The ISBN of the volume in Taiwan
        title_jp: The title of the comic in Japanese
        title_tw: The title of the comic in Taiwan
        author_tw: The author of the comic in Taiwan
        volume_number: The volume number of the volume
        release_date_tw: The release date of the volume in Taiwan
        publisher_tw: The publisher of the volume in Taiwan
        search_url: The URL of the search results page
        detail_url: The URL of the book detail page
    """
    # Anchor point for volume
    isbn_tw = scrapy.Field()

    # Anchor point for comic
    title_jp = scrapy.Field()

    # Comic fields
    title_tw = scrapy.Field()
    author_tw = scrapy.Field()

    # Volume fields
    volume_number = scrapy.Field()
    release_date_tw = scrapy.Field()
    publisher_tw = scrapy.Field()
    search_url = scrapy.Field()
    detail_url = scrapy.Field()


class JpComicItem(scrapy.Item):
    """
    Item for storing Japanese comic information

    Fields:
        title_jp: The title of the comic in Japanese
        author_jp: The author of the comic in Japanese
        status_jp: The status of the comic in Japanese
    """
    # Anchor point field
    title_jp = scrapy.Field()

    author_jp = scrapy.Field()
    status_jp = scrapy.Field()


class JpVolumeItem(scrapy.Item):
    """
    Item for storing Japanese volume information

    Fields:
        title_jp: The title of the comic in Japanese
        volume_number: The volume number of the volume
        release_date_jp: The release date of the volume in Japan
        isbn_jp: The ISBN of the volume in Japan
        publisher_jp: The publisher of the volume in Japan
    """
    # Anchor point field
    title_jp = scrapy.Field()

    volume_number = scrapy.Field()
    release_date_jp = scrapy.Field()
    isbn_jp = scrapy.Field()
    publisher_jp = scrapy.Field()
