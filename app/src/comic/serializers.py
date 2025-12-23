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
            "publisher",  # 出版社 ID (寫入用)
            "publisher_name",
        ]


class SeriesListSerializer(serializers.ModelSerializer):
    """
    漫畫清單的序列化器
    """

    traditional_chinese_title = serializers.CharField(source="title_tw")
    japanese_title = serializers.CharField(source="title_jp")
    status_japan = serializers.CharField(source="status_jp")

    author = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = [
            "id",
            "traditional_chinese_title",
            "japanese_title",
            "author",
            "status_japan",
        ]

    def get_author(self, obj):
        return obj.author_tw or obj.author_jp


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
