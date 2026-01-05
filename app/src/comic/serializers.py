from rest_framework import serializers

from .models import Publisher, Series, Volume


class PublisherSerializer(serializers.ModelSerializer):
    """
    出版社序列化器
    """

    class Meta:
        model = Publisher
        fields = ["id", "name", "region"]


class VolumeSerializer(serializers.ModelSerializer):
    """
    單行本序列化器
    """

    publisher_name = serializers.CharField(source="publisher.name", read_only=True)

    class Meta:
        model = Volume
        fields = [
            "id",
            "volume_number",
            "region",
            "variant",
            "release_date",
            "isbn",
            "image_url",
            "publisher",  # 出版社 ID (寫入用)
            "publisher_name",
        ]


class SeriesListSerializer(serializers.ModelSerializer):
    """
    漫畫清單的序列化器
    """

    # 計算欄位：整合作者資訊
    author = serializers.SerializerMethodField()

    # 計算欄位：最新單行本封面
    latest_volume_jp_image = serializers.SerializerMethodField()
    latest_volume_tw_image = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = [
            "id",
            "title_tw",
            "title_jp",
            "author_tw",
            "author_jp",
            "author",  # 計算欄位
            "status_jp",
            "latest_volume_jp_image",  # 計算欄位
            "latest_volume_tw_image",  # 計算欄位
        ]

    def get_author(self, obj):
        """整合的作者名稱（優先台灣譯名）"""
        return obj.author_tw or obj.author_jp

    def get_latest_volume_jp_image(self, obj):
        """日版最新單行本封面"""
        return obj.latest_volume_jp.image_url if obj.latest_volume_jp else None

    def get_latest_volume_tw_image(self, obj):
        """台版最新單行本封面"""
        return obj.latest_volume_tw.image_url if obj.latest_volume_tw else None


class SeriesDetailSerializer(SeriesListSerializer):
    """
    漫畫詳情的序列化器
    """

    # 巢狀引入 VolumeSerializer
    volumes = VolumeSerializer(many=True, read_only=True)

    latest_volume_jp_number = serializers.IntegerField(
        source="latest_volume_jp.volume_number", read_only=True, allow_null=True
    )
    latest_volume_tw_number = serializers.IntegerField(
        source="latest_volume_tw.volume_number", read_only=True, allow_null=True
    )

    class Meta(SeriesListSerializer.Meta):
        # 繼承 'fields' 並加上 'volumes'
        fields = SeriesListSerializer.Meta.fields + [
            "latest_volume_jp_number",
            "latest_volume_tw_number",
            "volumes",
        ]
