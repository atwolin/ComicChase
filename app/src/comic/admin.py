from django.contrib import admin

from .models import Publisher, Series, UserCollection, Volume


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
        "first_published_year",
        "latest_volume_tw_display",
    )
    list_filter = ("status_jp", "first_published_year")
    search_fields = ("title_jp", "title_tw", "author_jp", "author_tw")
    autocomplete_fields = ["latest_volume_jp", "latest_volume_tw"]
    inlines = [VolumeInline]
    fieldsets = (
        (
            "基本資訊",
            {
                "fields": (
                    "title_jp",
                    "title_tw",
                    "author_jp",
                    "author_tw",
                    "status_jp",
                )
            },
        ),
        (
            "分類與類型",
            {"fields": ("genres", "first_published_year")},
        ),
        (
            "最新單行本",
            {"fields": ("latest_volume_jp", "latest_volume_tw")},
        ),
    )

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
        "isbn",
    )
    # 依地區、出版社、發售日篩選
    list_filter = ("region", "release_date", "publisher")
    autocomplete_fields = ["series", "publisher"]
    search_fields = ("series__title_jp", "series__title_tw", "isbn")

    # 頁面欄位配置
    fieldsets = (
        (None, {"fields": ("series", "region", "volume_number", "variant")}),
        ("出版詳細資料", {"fields": ("publisher", "release_date", "isbn")}),
    )


@admin.register(UserCollection)
class UserCollectionAdmin(admin.ModelAdmin):
    list_display = ("user", "series", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "series__title_jp", "series__title_tw")
    autocomplete_fields = ["user", "series"]
    readonly_fields = ("created_at",)
