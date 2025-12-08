from django.contrib.auth.models import User
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Series, UserCollection
from .serializers import (
    SeriesDetailSerializer,
    SeriesListSerializer,
    UserCollectionSerializer,
    UserSerializer,
)


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    提供漫畫列表和漫畫詳情
    """

    # 優化查詢
    queryset = Series.objects.all().prefetch_related("volumes")

    # 搜尋搜尋與排序功能
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title_jp", "title_tw", "author_jp", "author_tw"]
    ordering_fields = ["id", "title_tw", "title_jp", "first_published_year"]
    ordering = ["-id"]  # 預設排序：最新更新

    def get_queryset(self):
        """
        根據 list 或 retrieve 動態優化資料庫查詢，並支持過濾
        """
        queryset = super().get_queryset()

        # 過濾條件
        status_jp = self.request.query_params.get("status_jp")
        genre = self.request.query_params.get("genre")
        year = self.request.query_params.get("year")

        if status_jp:
            queryset = queryset.filter(status_jp=status_jp)

        if genre:
            # 類型過濾支援部分匹配
            queryset = queryset.filter(genres__icontains=genre)

        if year:
            try:
                year_int = int(year)
                queryset = queryset.filter(first_published_year=year_int)
            except ValueError:
                pass

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


class UserCollectionViewSet(viewsets.ModelViewSet):
    """
    使用者收藏 ViewSet
    """

    serializer_class = UserCollectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回目前使用者的收藏"""
        return UserCollection.objects.filter(user=self.request.user).select_related(
            "series"
        )

    def perform_create(self, serializer):
        """建立收藏時自動設置使用者"""
        serializer.save(user=self.request.user)


class RegisterView(APIView):
    """
    使用者註冊
    """

    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")

        if not username or not password:
            return Response(
                {"error": "使用者名字和密碼是必需的"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "使用者名字已存在"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create_user(
                username=username, password=password, email=email
            )
        except Exception as e:
            return Response(
                {"error": f"建立使用者失敗: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "註冊成功", "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    """
    顯示目前使用者的資訊
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
