from django.contrib import admin
from .models import Publisher, Comic, Volume

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
    search_fields = ('name',)


@admin.register(Comic)
class ComicAdmin(admin.ModelAdmin):
    list_display = (
        'title_tw', 
        'title_jp', 
        'author_jp', 
        'author_tw',
        'status_jp',
        'publisher_japan_original'
    )
    list_filter = ('status_jp', 'publisher_japan_original')
    search_fields = (
        'title_jp', 
        'title_tw', 
        'author_jp',
        'author_tw'
    )


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    
    list_display = (
        'comic', 
        'volume_number', 
        'release_date_jp',
        'release_date_tw',
        'publisher_tw'     
    )
    list_filter = ('publisher_jp', 'publisher_tw')
    autocomplete_fields = ['comic', 'publisher_jp', 'publisher_tw'] # 修正
    search_fields = (
        'comic__title_jp',
        'comic__title_tw'  
    )
    