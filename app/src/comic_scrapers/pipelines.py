import re
from datetime import datetime

from comic.models import Publisher, Series, Volume
from django.db import IntegrityError
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from twisted.internet.threads import deferToThread

from comic_scrapers.items import JpComicItem, OrphanMapItem, OrphanVolumeItem


class ComicScrapersPipeline:
    """Pipeline to process scraped comic data items and store them into the database.

    This pipeline handles different types of scraped comic data items,
    routing them to appropriate processing methods based on their type.
    It uses `deferToThread` to offload database operations to a separate thread,
    preventing blocking of the Scrapy reactor.
    """

    ISBN_TW_REGEX = re.compile(r"ISBN13 / ([0-9]{13})")
    DATE_REGEX = re.compile(r"([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日")
    VOLUME_NUMBER_JP_REGEX = re.compile(r"[（(]?[0-9０-９]+[)）]?")
    ISBN_JP_REGEX = re.compile(r"([0-9]{13})")

    def process_item(self, item, spider):
        """See base class."""
        # Process data from books.com.tw
        if isinstance(item, OrphanVolumeItem):
            return deferToThread(self._process_orphan_volume_item, item, spider)

        # Process data from eslite.com
        elif isinstance(item, OrphanMapItem):
            if spider.name == "eslite_title_tw":
                return deferToThread(self._process_eslite_title_item, item, spider)
            return deferToThread(self._process_orphan_map_item, item, spider)

        # Process data from books.or.jp
        elif isinstance(item, JpComicItem):
            return deferToThread(self._process_jp_comic_item, item, spider)
        return item

    def _process_orphan_volume_item(self, item: OrphanVolumeItem, spider):
        """Process OrphanVolumeItem by ISBN to create new Volume entry in the database

        Args:
            item (OrphanVolumeItem): Item containing the extracted volume information.
            spider: The BooksTWSpider spider which scraped the item.

        Returns:
            OrphanVolumeItem: The processed item.

        Raises:
            DropItem: If processing fails due to missing data or database errors,
            including:
                - IntegrityError: If duplicate data is encountered in the database.
                - Exception: If any other error occurs during processing.
        """
        adapter = ItemAdapter(item)
        isbn_tw = adapter.get("isbn_tw")

        try:
            spider.logger.info(f"Processing Orphan Volume with ISBN {isbn_tw}")

            # Protect against missing ISBN
            if not isbn_tw:
                raise DropItem(
                    f"No isbn_tw in OrphanVolumeItem: \n{adapter.items()}\n{'-' * 50}"
                )

            # Create Volume entry in Volume Table
            obj, created = Volume.objects.get_or_create(
                isbn=isbn_tw,
                defaults={
                    "region": "TW",
                    "variant": "",
                },
            )
            if created:
                spider.logger.info(f"Created Orphan Volume with ISBN {isbn_tw}")
            else:
                spider.logger.warning(
                    f"Found existing Volume with ISBN {isbn_tw}, skipping"
                )

            return item

        except IntegrityError as e:
            spider.logger.warning(f"Duplicate data for ISBN {isbn_tw}: {str(e)}")
            raise DropItem(f"Duplicate Volume: {isbn_tw}") from e
        except DropItem:
            raise
        except Exception as e:
            spider.logger.error(
                f"Failed to process Orphan Volume with ISBN {isbn_tw}, error: {str(e)}",
                exc_info=True,
            )
            raise DropItem(f"Processing failed for Orphan Volume: {str(e)}") from e

    def _get_book_title_tw(self, book_title: str):
        """Process book_title_tw to extract title and volume number

        Because book titles from Books.com.tw may contain various suffixes indicating
        special editions or final volumes, this method parses the title to extract
        the core series name, volume number, and so on.
        Example formats:
            "最後一場閃爍的盛夏 (全)"
            "愚者之夜 9"
            "貓咪好夥伴小圓圓和小八 6 (特裝版)"
            "神速零零壹 2 (完)"
            "藍色時期 16 (首刷限定版)"
            "如果30歲還是處男, 似乎就能成為魔法師 15"
            "今日本貓依然貓威震主" (no volume number)

        Args:
            book_title (str): The full book title string from Books.com.tw.

        Returns:
            tuple: A tuple containing:
                - series_name_tw (str): The extracted series name in Chinese.
                - variant (str or None): The variant information if present.
                - volume_number (int or None): The extracted volume number if present.
                - is_final_volume (bool): True if the volume is marked as final.
        """
        parts = book_title.split(" ")
        # Series field
        series_name_tw = None
        is_final_volume = False
        # Volume field
        variant = None
        volume_number = None

        # Track whether we should remove the last part
        should_remove_last_part = False

        # Volume is special edition if "(特裝版)" found
        if len(parts) > 1 and "版" in parts[-1]:
            variant = parts[-1].strip("()")
            parts = parts[:-1]
            should_remove_last_part = False  # Already removed variant
        # Volume is final if "(完)" or "(全)" found
        elif len(parts) > 1 and parts[-1] == "(完)":
            is_final_volume = True
            parts = parts[:-1]
            should_remove_last_part = False  # Already removed completion marker
        elif len(parts) > 1 and parts[-1] == "(全)":
            is_final_volume = True
            should_remove_last_part = True  # Will handle below

        # Volume number == 1 if "1" or "(全)" found
        if parts[-1] in ["(全)", "1"]:
            volume_number = 1
            should_remove_last_part = True
        else:
            try:
                volume_number = int(parts[-1])
                should_remove_last_part = True
            except ValueError:
                volume_number = None
                should_remove_last_part = False

        # Only remove last part if we found a volume number or special marker
        if should_remove_last_part and len(parts) > 1:
            series_name_tw = " ".join(parts[:-1]).strip()
        else:
            # No volume number found, use entire title as series name
            series_name_tw = " ".join(parts).strip()

        return series_name_tw, variant, volume_number, is_final_volume

    def _process_orphan_map_item(self, item: OrphanMapItem, spider):
        """Process OrphanMapItem to link existing Comics with Volumes in the database

        OrphanMapItem contains volume information scraped from eslite.com,
        which is used to create or update Publisher and Series entries,
        and update existing Volume entries.

        Args:
            item (OrphanMapItem): Item containing the extracted volume information.
            spider: The EsliteSpider-based spider which scraped the item.

        Returns:
            OrphanMapItem: The processed item.

        Raises:
            DropItem: If processing fails due to missing data or database errors,
            including:
                - IntegrityError: If duplicate data is encountered in the database.
                - Exception: If any other error occurs during processing.
        """
        adapter = ItemAdapter(item)
        isbn_tw = adapter.get("isbn_tw")
        title_jp = adapter.get("title_jp")

        try:
            if not title_jp:
                raise DropItem(
                    f"No further information in OrphanMapItem:"
                    f"\n{adapter.items()}\n{'-' * 50}"
                )

            spider.logger.info(f"Processing Orphan Map Item for {title_jp}")

            search_query = adapter.get("search_query")

            # Use search_query to validate found ISBN
            if search_query and isbn_tw and search_query != isbn_tw:
                raise DropItem(
                    f"Search query ISBN '{search_query}' does not "
                    f"match found ISBN '{isbn_tw}'"
                )

            # Process Volume title and volume number
            title_tw = adapter.get("title_tw")
            if not title_tw:
                raise DropItem(f"No title_tw in OrphanMapItem: {adapter.items()}")

            (
                series_name_tw,
                variant,
                volume_number,
                is_final_volume,
            ) = self._get_book_title_tw(title_tw)

            author_tw_raw = adapter.get("author_tw")
            author_tw = (
                author_tw_raw.rsplit("\n", 1)[-1].strip() if author_tw_raw else ""
            )

            release_date_tw_raw = adapter.get("release_date_tw")
            release_date_tw = (
                release_date_tw_raw.rsplit("：", 1)[-1].strip().replace("/", "-")
                if release_date_tw_raw
                else ""
            )

            publisher_tw_raw = adapter.get("publisher_tw")
            publisher_tw = (
                publisher_tw_raw.rsplit("\n", 1)[-1].strip() if publisher_tw_raw else ""
            )

            # Extract image URL
            image_url_tw = adapter.get("image_url_tw", "")

            # Start storing data into database
            # 1. Get or create Publisher
            publisher, created_pub = Publisher.objects.get_or_create(
                name=publisher_tw, region="TW"
            )
            if created_pub:
                spider.logger.info(f"Created new Publisher: {publisher}")
            else:
                spider.logger.debug(f"Found existing Publisher: {publisher}")

            # 2. Get or create Series
            series, created_series = Series.objects.get_or_create(title_jp=title_jp)
            if created_series:
                spider.logger.info(f"Created new Series: {series}")
            else:
                spider.logger.debug(f"Found existing Series: {series}")
            # Update Series fields
            series.title_tw = series_name_tw
            series.author_tw = author_tw

            # 3. Update Volume
            volume = Volume.objects.filter(isbn=isbn_tw).first()
            if volume:
                volume.series = series
                volume.publisher = publisher
                volume.region = "TW"
                volume.volume_number = volume_number
                volume.variant = variant or ""
                volume.release_date = release_date_tw
                volume.image_url = image_url_tw
                volume.save()
                spider.logger.info(f"Updated Volume: {volume}")
            else:
                spider.logger.warning(
                    f"Volume with ISBN {isbn_tw} not found to update."
                )

            # Update series's latest_volume_tw if needed
            release_date_tw_obj = (
                datetime.strptime(release_date_tw, "%Y-%m-%d").date()
                if release_date_tw
                else None
            )
            if (
                is_final_volume
                or series.latest_volume_tw is None
                or (
                    release_date_tw_obj
                    and (
                        series.latest_volume_tw.release_date is None
                        or release_date_tw_obj > series.latest_volume_tw.release_date
                    )
                )
            ):
                # if is_final_volume:
                #     series.is_final_volume_tw = True
                series.latest_volume_tw = volume
                series.save()
                spider.logger.info(f"Updated Series latest_volume_tw: {series}")

            return item

        except IntegrityError as e:
            spider.logger.warning(f"Duplicate data for {title_jp}: {str(e)}")
            raise DropItem(f"Duplicate data: {str(e)}") from e
        except DropItem:
            raise
        except Exception as e:
            spider.logger.error(
                f"Failed to process Orphan Map Item for {title_jp}, error: {str(e)}",
                exc_info=True,
            )
            raise DropItem(f"Processing failed for Orphan Map Item: {str(e)}") from e

    def _process_eslite_title_item(self, item: OrphanMapItem, spider):
        """Process OrphanMapItem from EsliteTitleTwSpider

        This method handles items scraped by title search, which typically
        do not have an ISBN in the item fields but have it in product_desc.
        New volumes should be created if they don't exist.

        Args:
            item (OrphanMapItem): The scraped item.
            spider: The EsliteTitleTwSpider instance.
        """
        adapter = ItemAdapter(item)
        title_jp = adapter.get("title_jp")
        title_tw = adapter.get("title_tw")

        try:
            if not title_jp:
                raise DropItem(f"No title_jp in item: {adapter.items()}")

            spider.logger.info(f"Processing Eslite Title Item for {title_jp}")

            search_query = adapter.get("search_query")
            # Validate Title TW matches search query
            # Note: We check if search_query is in title_tw
            # because title_tw includes volume number etc.
            if search_query and title_tw and (search_query not in title_tw):
                raise DropItem(
                    f"Title TW '{title_tw}' does not contain "
                    f"search query '{search_query}'. Skipping."
                )

            # Extract ISBN from product_desc
            isbn_tw = None
            product_desc = adapter.get("product_desc")
            if product_desc:
                match = self.ISBN_TW_REGEX.search(product_desc)
                if match:
                    isbn_tw = match.group(1)

            if not isbn_tw:
                spider.logger.warning(
                    f"Could not extract ISBN for {title_jp}, skipping."
                )
                return item

            # Process Volume title and volume number
            if not title_tw:
                raise DropItem(f"No title_tw in item: {adapter.items()}")

            (
                series_name_tw,
                variant,
                volume_number,
                is_final_volume,
            ) = self._get_book_title_tw(title_tw)

            release_date_tw_raw = adapter.get("release_date_tw")
            release_date_tw = (
                release_date_tw_raw.rsplit("：", 1)[-1].strip().replace("/", "-")
                if release_date_tw_raw
                else ""
            )

            publisher_tw_raw = adapter.get("publisher_tw")
            publisher_tw = (
                publisher_tw_raw.rsplit("\n", 1)[-1].strip() if publisher_tw_raw else ""
            )

            # Extract image URL
            image_url_tw = adapter.get("image_url_tw", "")

            # 1. Get or create Publisher
            publisher, _ = Publisher.objects.get_or_create(
                name=publisher_tw, region="TW"
            )

            # 2. Get existing Series
            series = Series.objects.filter(title_tw=series_name_tw).first()
            if not series:
                spider.logger.warning(
                    f"Series not found for title_tw: {series_name_tw}, "
                    "skipping volume processing."
                )
                return item

            # 3. Get or create Volume
            volume, created = Volume.objects.get_or_create(
                isbn=isbn_tw,
                defaults={
                    "series": series,
                    "publisher": publisher,
                    "region": "TW",
                    "volume_number": volume_number,
                    "variant": variant or "",
                    "release_date": release_date_tw,
                    "image_url": image_url_tw,
                },
            )

            if created:
                spider.logger.info(f"Created new Volume: {volume}")
            else:
                # Update existing volume with latest info
                volume.series = series
                volume.publisher = publisher
                volume.volume_number = volume_number
                volume.variant = variant or ""
                volume.release_date = release_date_tw
                volume.image_url = image_url_tw
                volume.save()
                spider.logger.info(f"Updated existing Volume: {volume}")

            # Update series's latest_volume_tw
            release_date_tw_obj = (
                datetime.strptime(release_date_tw, "%Y-%m-%d").date()
                if release_date_tw
                else None
            )

            if (
                is_final_volume
                or series.latest_volume_tw is None
                or (
                    release_date_tw_obj
                    and series.latest_volume_tw.release_date
                    and release_date_tw_obj > series.latest_volume_tw.release_date
                )
            ):
                series.latest_volume_tw = volume
                series.save()
                spider.logger.info(f"Updated Series latest_volume_tw: {series}")

            return item

        except Exception as e:
            spider.logger.error(
                f"Failed to process Eslite Title Item for {title_jp}: {e}",
                exc_info=True,
            )
            raise DropItem(f"Processing title item failed: {e}") from e

    def _get_book_release_date_jp(self, product_desc: str):
        """Process product_desc to extract release date for the current volume.

        Because the date format in books.or.jp is in Japanese,
        we use a regex to extract the date components and reformat them to YYYY-MM-DD.
        Example formats:
            "発売予定日：2025年12月18日\n" -> "2025-12-18"
            "発売日：2018年12月06日\n" -> "2018-12-06"

        Args:
            product_desc (str): The product description containing the release date.

        Returns:
            str: The release date in YYYY-MM-DD format.
        """
        match = self.DATE_REGEX.search(product_desc)
        if match:
            year, month, day = match.groups()
            # Pad month and day with leading zeros to ensure 2 digits
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None

    def _get_book_title_jp(self, book_title: str, series_name_jp: str):
        """Process title to extract volume number for Japanese comics

        Because book titles from books.or.jp may contain various suffixes indicating
        special editions or final volumes, this method parses the title to extract
        the core series name, volume number, and so on.
        Example formats:
            "廻天のアルバス ７"
            "ブルーピリオド（18）"
            "ブルーピリオド（1）実写映画化記念特装版"

        Args:
            book_title (str): The full book title string from books.or.jp.
            series_name_jp (str): The series name in Japanese.

        Returns:
            tuple: A tuple containing:
                - variant (str or None): The variant information if present, else None.
                - volume_number (int or None): The extracted volume number
                                               if present, else None.
        """
        matches = self.VOLUME_NUMBER_JP_REGEX.findall(book_title)
        if matches:
            volume_number = matches[-1]
            variant = book_title.replace(series_name_jp, "").strip()
            variant = variant.replace(volume_number, "").strip()
            volume_number = int(volume_number.strip("()（）").strip())
            return variant, volume_number
        return None, None

    def _process_jp_comic_item(self, item: JpComicItem, spider):
        """Process JpComicItem to update or create Series and Volume entry.

        JpComicItem contains volume information scraped from books.or.jp,
        which is used to create or update Publisher and Series entries,
        and create new Volume entries.

        Args:
            item (JpComicItem): Item containing the extracted volume information.
            spider: The JpComicSpider spider which scraped the item.

        Returns:
            JpComicItem: The processed item.

        Raises:
            DropItem: If processing fails due to missing data or database errors,
            including:
                - IntegrityError: If duplicate data is encountered in the database.
                - Exception: If any other error occurs during processing.
        """
        adapter = ItemAdapter(item)
        detail_url = adapter.get("detail_url")
        series_name_jp = adapter.get("search_query")

        try:
            if not detail_url:
                raise DropItem(
                    f"No further information in JpComicItem:"
                    f"\n{adapter.items()}\n{'-' * 50}"
                )

            if not series_name_jp:
                raise DropItem(
                    f"No search_query in JpComicItem:\n{adapter.items()}\n{'-' * 50}"
                )

            spider.logger.info(f"Processing JP Comic Item: {series_name_jp}")

            title_jp_raw = adapter.get("title_jp")
            spider.logger.debug(f"Processing JP Comic Item Title {title_jp_raw}")

            if not title_jp_raw:
                raise DropItem(
                    f"No title_jp in JpComicItem:\n{adapter.items()}\n{'-' * 50}"
                )

            if not title_jp_raw.startswith(series_name_jp):
                raise DropItem(
                    f"Title JP does not start with series name in JpComicItem:"
                    f"\n{adapter.items()}\n{'-' * 50}"
                )

            isbn_jp = detail_url.rsplit("/", 1)[-1].strip()
            if self.ISBN_JP_REGEX.match(isbn_jp) is None:
                # One episode, not a full volume
                raise DropItem(
                    f"Invalid ISBN_JP in JpComicItem: \n{adapter.items()}\n{'-' * 50}"
                )

            publisher_jp_raw = adapter.get("publisher_jp")
            publisher_jp = (
                publisher_jp_raw.rsplit("出版社：", 1)[-1].strip()
                if publisher_jp_raw
                else ""
            )

            author_jp_raw = adapter.get("author_jp")
            author_jp = author_jp_raw[2:] if author_jp_raw else []
            author_jp_str = "; ".join(author_jp) if author_jp else ""
            # status_jp = ""
            variant, volume_number = self._get_book_title_jp(
                title_jp_raw, series_name_jp
            )

            product_desc = adapter.get("product_desc")
            release_date_jp = self._get_book_release_date_jp(
                product_desc if product_desc else ""
            )

            # Extract image URL
            image_url_jp = adapter.get("image_url_jp", "")

            # Start storing data into database
            # 1. Get or create Publisher
            publisher, created_pub = Publisher.objects.get_or_create(
                name=publisher_jp, region="JP"
            )
            if created_pub:
                spider.logger.info(f"Created new Publisher: {publisher}")
            else:
                spider.logger.debug(f"Found existing Publisher: {publisher}")

            # 2. Get or create Series
            series, created_series = Series.objects.get_or_create(
                title_jp=series_name_jp,
            )
            if created_series:
                spider.logger.info(f"Created new Series: {series}")
            else:
                spider.logger.debug(f"Found existing Series: {series}")
            # Update Series fields
            series.author_jp = author_jp_str
            series.save()

            # 3. Update Volume
            volume, created_volume = Volume.objects.get_or_create(
                isbn=isbn_jp,
                defaults={
                    "series": series,
                    "publisher": publisher,
                    "region": "JP",
                    "volume_number": volume_number,
                    "variant": variant or "",
                    "release_date": release_date_jp,
                    "image_url": image_url_jp,
                },
            )
            if created_volume:
                spider.logger.info(f"Created Volume: {volume}")
            else:
                spider.logger.warning(
                    f"Found existing Volume with ISBN {isbn_jp}, skipping"
                )

            # Update series's latest_volume_jp if needed
            release_date_jp_obj = (
                datetime.strptime(release_date_jp, "%Y-%m-%d").date()
                if release_date_jp
                else None
            )
            if series.latest_volume_jp is None or (
                release_date_jp_obj
                and (
                    series.latest_volume_jp.release_date is None
                    or release_date_jp_obj > series.latest_volume_jp.release_date
                )
            ):
                series.latest_volume_jp = volume
                series.save()
                spider.logger.info(f"Updated Series latest_volume_jp: {series}")

            return item

        except IntegrityError as e:
            spider.logger.warning(f"Duplicate data for {series_name_jp}: {str(e)}")
            raise DropItem(f"Duplicate Volume: {str(e)}") from e
        except DropItem:
            raise
        except Exception as e:
            spider.logger.error(
                "Failed to process JP Comic Item for "
                f"{series_name_jp}, error: {str(e)}",
                exc_info=True,
            )
            raise DropItem(f"Processing failed for JP Comic Item: {str(e)}") from e
