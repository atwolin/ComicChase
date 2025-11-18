from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from .models import Comic
from .serializers import ComicListSerializer, ComicDetailSerializer

class ComicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    提供漫畫列表和漫畫詳情
    """
    # 優化查詢
    queryset = Comic.objects.all().prefetch_related('volumes') 

    # 搜尋日文或中文標題
    filter_backends = [SearchFilter]
    search_fields = ['title_jp', 'title_tw'] 

    def get_serializer_class(self):
        """
        選擇 'list' (列表) or 'retrieve' (詳情)
        """
        if self.action == 'list':
            return ComicListSerializer
        return ComicDetailSerializer
