import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

app = Celery("comicchase")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # "crawl-bookstw-new-releases": {
    #     "task": "comic_scrapers.tasks.crawl_new_volumes_bookstw",
    #     # "schedule": crontab(minute=0, hour=2)
    #     "schedule": crontab(minute="48", hour="*"),  # TESTING: Every hour
    # },
    # "crawl-eslite-by-isbn": {
    #     "task": "comic_scrapers.tasks.crawl_orphan_volumes_eslite",
    #     # "schedule": crontab(minute=0, hour=3)
    #     "schedule": crontab(minute="52", hour="*"),  # TESTING: Every hour
    # },
    # "crawl-eslite-by-title": {
    #     "task": "comic_scrapers.tasks.crawl_all_series_eslite",
    #     # "schedule": crontab(minute=0, hour=4)
    #     "schedule": crontab(minute="57", hour="*"),  # TESTING: Every hour
    # },
    # "crawl-booksjp-by-title": {
    #     "task": "comic_scrapers.tasks.crawl_all_series_booksjp",
    #     # "schedule": crontab(minute=0, hour=5)
    #     "schedule": crontab(minute="02", hour="*"),  # TESTING: Every hour
    # },
    "send-weekly-digest-every-friday": {
        "task": "subscriptions.tasks.run_weekly_notification_flow",
        # "schedule": crontab(hour=12, minute=0, day_of_week="friday"),
        "schedule": crontab(minute="00", hour="*"),  # TESTING: Every hour
    }
}
