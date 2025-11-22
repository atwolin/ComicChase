# Comic Scrapers

Django management commands for scraping comic data from various sources.

## Available Commands

### 1. `booktw_crawl`
Crawls books.com.tw for orphan volumes (volumes not yet linked to a series).

**Usage:**
```bash
docker compose exec web python manage.py booktw_crawl
```

**What it does:**
- Scrapes the books.com.tw new releases page
- Extracts ISBN information for Taiwanese volumes
- Processes up to 100 book links from the new releases section
- Uses `BooksTWSpider` to collect orphan volume data

**Spider:** `BooksTWSpider` in `spiders/books_tw.py`

---

### 2. `eslite_isbn_crawl`
Crawls eslite.com to map orphan Taiwanese volumes using ISBN lookup.

**Usage:**
```bash
docker compose exec web python manage.py eslite_isbn_crawl
```

**What it does:**
- Searches eslite.com using ISBNs from orphan volumes (TW region)
- Extracts detailed volume and series information
- Matches volumes with series data including titles, authors, and publishers
- Uses Selenium for dynamic page interaction

**Spider:** `EsliteISBNSpider` in `spiders/eslite.py`

**Data extracted:**
- Japanese title (`title_jp`)
- Taiwanese title (`title_tw`)
- Author (TW)
- Publisher (TW)
- Release date (TW)
- Product description

---

### 3. `bookjp_title_crawl`
Crawls books.or.jp to update Japanese comic titles and author information.

**Usage:**
```bash
docker compose exec web python manage.py bookjp_title_crawl
```

**What it does:**
- Searches books.or.jp using existing Japanese titles from the database
- Updates series information with author details
- Targets series that have Japanese titles but missing author information
- Uses Selenium for dynamic search and navigation

**Spider:** `BooksJpTitleTwSpider` in `spiders/books_jp.py`

**Data extracted:**
- Japanese title (`title_jp`)
- Japanese author(s) (`author_jp`)
- Japanese publisher (`publisher_jp`)
- Product description

---

## Requirements

These commands require:
- Docker and Docker Compose running
- Selenium service configured (for `eslite_isbn_crawl` and `bookjp_title_crawl`)
- PostgreSQL database with the `comic` app models
- Scrapy configured with appropriate settings

## Notes

- All commands use Scrapy's `CrawlerProcess` to run spiders
- Commands that use Selenium (`eslite_isbn_crawl`, `bookjp_title_crawl`) connect to a remote Selenium service at `http://selenium:4444/wd/hub`
- Scraped data is processed through Scrapy pipelines defined in `pipelines.py`
- Commands include sleep delays to respect rate limits and avoid overwhelming target sites
