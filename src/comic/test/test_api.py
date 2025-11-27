from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


from comic.models import Publisher, Series, Volume




class SeriesAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.publisher = Publisher.objects.create(name="東立", region=Publisher.Region.TAIWAN)
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
        url = reverse("comics-list")
        response = self.client.get(url)


        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 1)


    def test_pagination_respects_page_size(self):
        for idx in range(12):
            Series.objects.create(
                title_jp=f"テスト作品{idx}",
                author_jp="作者",
            )
        url = reverse("comics-list")
        response = self.client.get(url)


        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])


    def test_search_filters_by_titles(self):
        url = reverse("comics-list")
        response = self.client.get(url, {"search": "巨人"})


        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.series.id, ids)


    def test_search_can_return_empty_results(self):
        url = reverse("comics-list")
        response = self.client.get(url, {"search": "不存在"})


        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


    def test_detail_endpoint_includes_volumes(self):
        url = reverse("comics-detail", args=[self.series.id])
        response = self.client.get(url)


        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("volumes", response.data)
        self.assertEqual(len(response.data["volumes"]), 1)


    def test_detail_endpoint_returns_404_for_missing_series(self):
        url = reverse("comics-detail", args=[9999])
        response = self.client.get(url)


        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_readonly_permission_allows_anonymous_get(self):
        url = reverse("comics-list")
        response = self.client.get(url)


        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_write_operation_denied_for_anonymous(self):
        url = reverse("comics-list")
        payload = {
            "title_jp": "新作品",
            "author_jp": "作者",
        }
        response = self.client.post(url, payload, format="json")


        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
