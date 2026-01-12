import random

from comic.models import Series
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "產生 10,000 筆漫畫系列測試資料"

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            self.stderr.write(
                self.style.ERROR("This command can only run with DEBUG=True")
            )
            return

        self.stdout.write("正在清理舊資料...")
        Series.objects.all().delete()

        self.stdout.write("開始產生 10,000 筆資料...")

        series_list = []

        # 混入一些包含巨人的標題
        test_keywords = ["進擊的巨人", "巨人中學", "九大巨人", "進擊巨人", "巨人遺孤"]

        for i in range(10000):
            # 隨機產生標題(前 100 筆包含關鍵字)
            if i < 100:
                title = f"{random.choice(test_keywords)} - {i}"
            else:
                title = f"漫畫作品樣本第 {i} 號"

            series_list.append(
                Series(
                    title_jp=f"Sample Comic JP {i}",
                    title_tw=title,
                    author_jp=f"Author JP {i}",
                    author_tw=f"作者 {i}",
                )
            )

            # 避免記憶體溢位
            if len(series_list) >= 2000:
                Series.objects.bulk_create(series_list)
                series_list = []
                self.stdout.write(f"已完成 {i+1} 筆...")

        if series_list:
            Series.objects.bulk_create(series_list)

        self.stdout.write(self.style.SUCCESS("成功新增 10,000 筆資料！"))
