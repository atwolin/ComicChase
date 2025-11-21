from django.contrib import admin
from .models import Publisher, Series, Volume

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Series)
class ComicAdmin(admin.ModelAdmin):
    list_display = (
        'title_tw',
        'title_jp',
        'latest_volume_number_jp',
        'latest_volume_number_tw',
        'status_jp'
    )
    list_filter = ('status_jp',)
    search_fields = (
        'title_jp',
        'title_tw',
        'author_jp',
        'author_tw'
    )
    readonly_fields = (
        'latest_volume_number_jp',
        'latest_release_date_jp',
        'latest_volume_number_tw',
        'latest_release_date_tw',
    )


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):

    list_display = (
        'series',
        'volume_number',
        'region',
        'variant',
        'release_date',
        'publisher',
        'isbn'
    )
    #依地區、出版社、發售日篩選
    list_filter = ('region', 'release_date', 'publisher')
    autocomplete_fields = ['series', 'publisher']
    search_fields = (
        'series__title_jp',
        'series__title_tw',
        'isbn'
    )

    #頁面欄位配置
    fieldsets = (
        (None, {
            'fields': ('comic', 'region', 'volume_number', 'variant')
        }),
        ('出版詳細資料', {
            'fields': ('publisher', 'release_date', 'isbn')
        }),
    )
