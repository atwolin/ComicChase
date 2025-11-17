from rest_framework import serializers
from .models import Comic, Volume

class VolumeSerializer(serializers.ModelSerializer):
    """
    Volume 序列化器
    """

    release_date_japan = serializers.DateField(source='release_date_jp')
    release_date_taiwan = serializers.DateField(source='release_date_tw')
    
    class Meta:
        model = Volume
        fields = [
            'volume_number', 
            'release_date_japan', 
            'release_date_taiwan'
        ]

class ComicListSerializer(serializers.ModelSerializer):
    """
    漫畫清單的序列化器
    """
    
    traditional_chinese_title = serializers.CharField(source='title_tw')
    japanese_title = serializers.CharField(source='title_jp')
    status_japan = serializers.CharField(source='status_jp')
    
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comic
        fields = [
            'id', 
            'traditional_chinese_title', 
            'japanese_title', 
            'author', 
            'status_japan'
        ]

    def get_author(self, obj):
        return obj.author_tw or obj.author_jp


class ComicDetailSerializer(ComicListSerializer):
    """
    漫畫詳情的序列化器
    """
    # 巢狀引入 VolumeSerializer
    volumes = VolumeSerializer(many=True, read_only=True)

    class Meta(ComicListSerializer.Meta):
        # 繼承 'fields' 並加上 'volumes'
        fields = ComicListSerializer.Meta.fields + ['volumes']