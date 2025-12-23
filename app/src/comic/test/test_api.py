from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from comic.models import Publisher, Series, Volume


class SeriesAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create test data for the entire TestCase"""
        cls.publisher = Publisher.objects.create(
            name="東立", region=Publisher.Region.TAIWAN
        )
        cls.series = Series.objects.create(
            title_jp="進撃の巨人",
            title_tw="進擊的巨人",
            author_jp="諫山創",
            author_tw="諫山創",
            status_jp=Series.JapanStatus.COMPLETED,
        )
        cls.volume = Volume.objects.create(
            series=cls.series,
            publisher=cls.publisher,
            region=Volume.Region.TAIWAN,
            volume_number=34,
            isbn="9789861234567",
        )

    def test_list_endpoint_returns_series(self):
        """測試列出所有系列漫畫"""
        url = reverse("series-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_pagination_respects_page_size(self):
        """測試分頁功能"""
        for idx in range(12):  # 建立 12 筆資料觸發分頁
            Series.objects.create(
                title_jp=f"テスト作品{idx}",
                author_jp="作者",
            )
        url = reverse("series-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)  # 確保每頁只有 10 筆
        self.assertIsNotNone(response.data["next"])

    def test_search_filters_by_titles(self):
        """測試搜尋功能可依標題過濾"""
        url = reverse("series-list")
        response = self.client.get(url, {"search": "巨人"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.series.id, ids)

    def test_search_can_return_empty_results(self):
        """測試空結果的處理"""
        url = reverse("series-list")
        response = self.client.get(url, {"search": "不存在"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_detail_endpoint_includes_volumes(self):
        """測試回傳詳細資訊及關聯單行本"""
        url = reverse("series-detail", args=[self.series.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("volumes", response.data)
        self.assertEqual(len(response.data["volumes"]), 1)

    def test_detail_endpoint_returns_404_for_missing_series(self):
        """測試不存在的 ID 回傳 404"""
        url = reverse("series-detail", args=[9999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_readonly_permission_allows_anonymous_get(self):
        """測試未認證用戶可以唯讀"""
        url = reverse("series-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_write_operation_not_allowed(self):
        """測試 API 為唯讀，不允許寫入操作"""
        url = reverse("series-list")
        payload = {
            "title_jp": "新作品",
            "title_tw": "新作品",
            "author_jp": "作者",
            "author_tw": "作者",
            "status_jp": Series.JapanStatus.ONGOING,
        }

        # 測試匿名用戶 - IsAuthenticatedOrReadOnly 會先檢查權限
        self.client.force_authenticate(user=None)
        response_anonymous = self.client.post(url, payload, format="json")
        self.assertEqual(
            response_anonymous.status_code,
            status.HTTP_403_FORBIDDEN,
            "匿名用戶嘗試 POST 應該回傳 403 Forbidden (IsAuthenticatedOrReadOnly)",
        )

        # 測試已認證用戶 - ReadOnlyModelViewSet 不支援 POST
        user = get_user_model().objects.create_user(
            username="testuser", email="testuser@example.com", password="testpass"
        )
        self.client.force_authenticate(user=user)
        response_authenticated = self.client.post(url, payload, format="json")
        self.assertEqual(
            response_authenticated.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            "已認證用戶嘗試 POST 應該回傳 405 Method Not Allowed"
            " (ReadOnlyModelViewSet)",
        )
