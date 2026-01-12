import scrapy


class OrphanVolumeItem(scrapy.Item):
    """
    Item for volumes that do not have an associated comic yet

    Fields:
        isbn_tw: The ISBN of the volume in Taiwan
        search_query: The target used to find the respective book
        source_url: The URL of the source page
    """

    # Anchor point field
    isbn_tw = scrapy.Field()

    search_query = scrapy.Field()
    source_url = scrapy.Field()


class OrphanMapItem(scrapy.Item):
    """
    Item for mapping volume to comic when new volume found without associated comic

    Fields:
        isbn_tw: The ISBN of the volume in Taiwan
        title_jp: The title of the comic in Japanese
        title_tw: The title of the comic in Taiwan
        author_tw: The author of the comic in Taiwan
        release_date_tw: The release date of the volume in Taiwan
        publisher_tw: The publisher of the volume in Taiwan
        search_query: The target used to find the respective book
        search_url: The URL of the search results page
        detail_url: The URL of the book detail page
        product_desc: The product description of the volume
    """

    # Anchor point for volume
    isbn_tw = scrapy.Field()

    # Anchor point for comic
    title_jp = scrapy.Field()

    # Comic fields
    title_tw = scrapy.Field()
    author_tw = scrapy.Field()

    # Volume fields
    release_date_tw = scrapy.Field()
    publisher_tw = scrapy.Field()
    image_url_tw = scrapy.Field()

    # Metadata fields
    search_query = scrapy.Field()
    search_url = scrapy.Field()
    detail_url = scrapy.Field()
    product_desc = scrapy.Field()


class JpComicItem(scrapy.Item):
    """
    Item for storing Japanese comic information

    Fields:
        title_jp: The title of the comic in Japanese
        author_jp: The author of the comic in Japanese
        publisher_jp: The publisher of the comic in Japan
        search_query: The target used to find the respective book
        detail_url: The URL of the book detail page
        product_desc: The product description of the comic
    """

    # Anchor point field
    title_jp = scrapy.Field()

    # Comic fields
    author_jp = scrapy.Field()

    # Volume fields
    publisher_jp = scrapy.Field()
    image_url_jp = scrapy.Field()

    # Metadata fields
    search_query = scrapy.Field()
    detail_url = scrapy.Field()
    product_desc = scrapy.Field()
