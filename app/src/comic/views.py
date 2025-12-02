from rest_framework import filters, viewsets

from .models import Series
from .serializers import SeriesDetailSerializer, SeriesListSerializer


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    提供漫畫列表和漫畫詳情
    """

    # 優化查詢
    queryset = Series.objects.all().prefetch_related("volumes")

    # 搜尋搜尋與排序功能
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title_jp", "title_tw", "author_jp", "author_tw"]
    ordering_fields = ["title_tw", "title_jp"]
    ordering = ["title_tw"]  # 預設排序

    def get_queryset(self):
        """
        根據 list 或 retrieve 動態優化資料庫查詢
        """
        queryset = super().get_queryset()

        if self.action == "retrieve":
            # === 詳細頁面 (Detail View) ===
            return queryset.select_related(
                # 抓取關聯的「最新單行本」資訊，避免額外查詢
                "latest_volume_jp",
                "latest_volume_tw",
            ).prefetch_related("volumes__publisher")

        # === 列表頁面 (List View) ===
        # 只列 Series 本身的文字資訊，維持輕量化
        return queryset

    def get_serializer_class(self):
        """
        選擇 'list' (列表) or 'retrieve' (詳情)
        """
        if self.action == "list":
            return SeriesListSerializer
        return SeriesDetailSerializer
