# Comic Scrapers

Django management commands and Celery tasks for scraping comic data from various sources.

## Available Management Commands

Use these commands for manual execution or testing specific crawls.

### 1. `books_tw_new_releases`
Crawls books.com.tw for orphan volumes (volumes not yet linked to a series).

**Usage:**
```bash
docker compose exec web python manage.py books_tw_new_releases
```

**What it does:**
- Scrapes the books.com.tw new releases page
- Extracts ISBN information for Taiwanese volumes
- Uses `BooksTWSpider` to collect orphan volume data

**Spider:** `BooksTWSpider` in `spiders/books_tw.py`

---

### 2. `eslite_isbn_search`
Crawls eslite.com to map a specific orphan Taiwanese volume using ISBN lookup.

**Usage:**
```bash
docker compose exec web python manage.py eslite_isbn_search --isbn "978xxxxxxxxxx"
```

**What it does:**
- Searches eslite.com using the provided ISBN
- Extracts detailed volume and series information
- Matches volume with series data including titles, authors, and publishers

**Spider:** `EsliteISBNSpider` in `spiders/eslite.py`

---

### 3. `books_jp_title_search`
Crawls books.or.jp to update Japanese comic titles and author information for a specific series.

**Usage:**
```bash
docker compose exec web python manage.py books_jp_title_search --title "Series Title JP" --last-release-date "YYYY-MM-DD"
```

**What it does:**
- Searches books.or.jp using the provided Japanese title
- Updates series information with author details
- Useful for series that have Japanese titles but missing author information

**Spider:** `BooksJpTitleTwSpider` in `spiders/books_jp.py`

---

### 4. `eslite_title_search`
Crawls eslite.com to search and extract volumes for a specific series by Taiwanese title.

**Usage:**
```bash
docker compose exec web python manage.py eslite_title_search --title "Series Title TW" --last-release-date "YYYY-MM-DD"
```

**What it does:**
- Searches eslite.com using the provided Taiwanese series title
- Extracts volume information for the series
- Can optionally filter by last release date to skip existing volumes

**Spider:** `EsliteTitleTwSpider` in `spiders/eslite.py`

---

## Celery Tasks (Bulk Crawling)

For production and bulk updates, use the available Celery tasks. These tasks handle database querying and distribute crawling jobs.

### Available Tasks
These are defined in `tasks.py`:

- **`crawl_new_volumes_bookstw`**:
    - Wraps `books_tw_new_releases` command.
    - Crawls new releases list.

- **`crawl_orphan_volumes_eslite`**:
    - Queries all orphan volumes (volumes with ISBN but no Series) from the database.
    - Spawns parallel `crawl_single_isbn_eslite` tasks for each ISBN.

- **`crawl_all_series_eslite`**:
    - Queries all series with Traditional Chinese titles.
    - Spawns parallel `crawl_single_title_eslite` tasks for each series.

- **`crawl_all_series_booksjp`**:
    - Queries all series with Japanese titles.
    - Spawns parallel `crawl_single_title_booksjp` tasks for each series.

### Triggering Tasks
You can trigger these tasks via the Django shell:

```python
from comic_scrapers.tasks import crawl_orphan_volumes_eslite
crawl_orphan_volumes_eslite.delay()
```

---

## Requirements

These commands require:
- Docker and Docker Compose running
- Selenium service configured (for `eslite` spiders and `books_jp` spiders)
- PostgreSQL database with the `comic` app models
- Scrapy configured with appropriate settings

## Notes

- Management commands use Scrapy's `CrawlerProcess` to run spiders.
- Commands that use Selenium connect to a remote Selenium service at `http://selenium:4444/wd/hub`.
- Scraped data is processed through Scrapy pipelines defined in `pipelines.py`.
