from django.contrib import admin
from .models import Publisher, Series, Volume, VolumeJp, VolumeTw

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
    search_fields = ('name',)


@admin.register(Series)
class ComicAdmin(admin.ModelAdmin):
    list_display = (
        'title_tw',
        'title_jp',
        'author_jp',
        'author_tw',
        'status_jp'
    )
    list_filter = ('status_jp',)
    search_fields = (
        'title_jp',
        'title_tw',
        'author_jp',
        'author_tw'
    )


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):

    list_display = (
        'series',
        'volume_number',
        'release_date_jp',
        'release_date_tw',
        'publisher_tw'
    )
    list_filter = ('publisher_jp', 'publisher_tw')
    autocomplete_fields = ['series', 'publisher_jp', 'publisher_tw'] # 修正
    search_fields = (
        'series__title_jp',
        'series__title_tw'
    )

@admin.register(VolumeJp)
class VolumeJpAdmin(admin.ModelAdmin):
    list_display = (
        'title_jp',
        'volume_number',
        'isbn_jp',
        'release_date_jp',
        'publisher_jp',
        'series'
    )
    list_filter = ('publisher_jp',)
    autocomplete_fields = ['series', 'publisher_jp']
    search_fields = (
        'series__title_jp',
    )

@admin.register(VolumeTw)
class VolumeTwAdmin(admin.ModelAdmin):
    list_display = (
        'title_tw',
        'volume_number',
        'isbn_tw',
        'release_date_tw',
        'publisher_tw',
        'series'
    )
    list_filter = ('publisher_tw',)
    autocomplete_fields = ['series', 'publisher_tw']
    search_fields = (
        'series__title_tw',
    )
