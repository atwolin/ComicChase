from urllib.parse import urlparse

from django.contrib import admin
from django.utils.html import format_html

from .models import Publisher, Series, Volume


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "region")
    list_filter = ("region",)
    search_fields = ("name",)
    ordering = ("name",)


class VolumeInline(admin.TabularInline):
    model = Volume
    extra = 0
    fields = ("volume_number", "region", "variant", "release_date", "publisher", "isbn")
    autocomplete_fields = ["publisher"]
    show_change_link = True


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = (
        "title_tw",
        "title_jp",
        "status_jp",
        "latest_volume_tw_display",
        "latest_volume_jp",
    )
    list_filter = ("status_jp",)
    search_fields = ("title_jp", "title_tw", "author_jp", "author_tw")
    autocomplete_fields = ["latest_volume_jp", "latest_volume_tw"]
    inlines = [VolumeInline]

    @admin.display(description="最新單行本 (台)")
    def latest_volume_tw_display(self, obj):
        return obj.latest_volume_tw


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    list_display = (
        "series",
        "volume_number",
        "region",
        "variant",
        "release_date",
        "publisher",
        "cover_image_thumbnail",
        "isbn",
    )
    # 依地區、出版社、發售日篩選
    list_filter = ("region", "release_date", "publisher")
    autocomplete_fields = ["series", "publisher"]
    search_fields = ("series__title_jp", "series__title_tw", "isbn")

    # 頁面欄位配置
    fieldsets = (
        (None, {"fields": ("series", "region", "volume_number", "variant")}),
        (
            "出版詳細資料",
            {"fields": ("publisher", "release_date", "isbn", "image_url")},
        ),
    )

    @admin.display(description="封面圖片")
    def cover_image_thumbnail(self, obj):
        """Display a thumbnail of the cover image in the admin list view."""
        if obj.image_url:
            # Validate URL scheme to prevent XSS attacks (defense in depth)
            parsed_url = urlparse(obj.image_url)
            allowed_schemes = ["http", "https"]

            if parsed_url.scheme and parsed_url.scheme.lower() in allowed_schemes:
                return format_html(
                    '<img src="{}" style="height: 100px; object-fit: contain;" />',
                    obj.image_url,
                )
            else:
                # Return error message if URL scheme is not allowed
                return format_html('<span style="color: red;">⚠️ 不安全的 URL</span>')
        return "—"
