from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from comic.models import Series


class SeriesSearchTests(APITestCase):
    """
    測試 Series 的 Trigram 搜尋功能與排序邏輯
    """

    def setUp(self):
        # 建立測試資料
        self.series1 = Series.objects.create(
            title_tw="進擊的巨人", title_jp="進撃の巨人"
        )
        self.series2 = Series.objects.create(
            title_tw="巨人族的新娘", title_jp="巨人族の花嫁"
        )
        self.series3 = Series.objects.create(title_tw="海賊王", title_jp="ONE PIECE")
        self.url = reverse("series-list")

    def test_search_by_trigram_similarity(self):
        """
        測試搜尋「巨人」時，是否能正確命中包含相似字根的標題
        """
        response = self.client.get(self.url, {"search": "巨人"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        titles = [
            item["traditional_chinese_title"] for item in response.data["results"]
        ]
        self.assertIn("進擊的巨人", titles)
        self.assertIn("巨人族的新娘", titles)
        # 預期「海賊王」不會出現
        self.assertNotIn("海賊王", titles)

    def test_search_ordering_by_similarity(self):
        """
        測試搜尋結果是否按照相似度分數由高到低排序
        """
        # 當搜尋「進擊的巨人」時，進擊的巨人排在第一
        response = self.client.get(self.url, {"search": "進擊的巨人"})

        self.assertTrue(
            response.data["results"], "搜尋結果為空，可能是 Trigram 設定問題"
        )
        first_result_title = response.data["results"][0]["traditional_chinese_title"]
        self.assertEqual(first_result_title, "進擊的巨人")

    def test_search_threshold_filtering(self):
        """
        測試相似度門檻是否有效過濾無關資料
        """
        # 搜尋一個完全無關的詞
        response = self.client.get(self.url, {"search": "計算機概論"})

        self.assertEqual(len(response.data["results"]), 0)

    def test_empty_search_returns_all(self):
        """
        測試當搜尋參數為空時，應回傳原始 QuerySet (不進行相似度過濾）
        """
        response = self.client.get(self.url, {"search": ""})
        self.assertEqual(len(response.data["results"]), 3)
