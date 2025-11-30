# Comic Scrapers Tests

This directory contains unit tests for the Comic Scrapers project, which scrapes comic book information from various sources.

## Test Files Overview

### 1. `test_books_tw.py`
Tests for the **BooksTW spider** that scrapes comic information from books.com.tw.

**Covers:**
- Parse method (main entry point)
- Volume info parsing with ISBN extraction
- Handling of EPUB volumes (should be ignored)
- One-volume series detection
- Forthcoming/pre-order volume handling

**Test fixtures:**
- `test_books_tw_epub_page.html` - Sample EPUB page
- `test_books_tw_forthcoming_page.html` - Pre-order page
- `test_books_tw_one_volume_page.html` - Single volume page
- `test_books_tw_result.json` - Expected results

### 2. `test_eslite.py`
Tests for the **Eslite spider** that scrapes comic information from eslite.com (誠品書店).

**Covers:**
- Search results parsing with category filtering
- Detail page information extraction
- Multiple URL processing from search results
- Book title, author, release date, and publisher extraction
- Handling of items without Japanese titles

**Key features:**
- Selenium WebDriver mocking for dynamic page interaction
- Category filter clicking simulation
- URL refresh after processing each item

### 3. `test_books_jp.py`
Tests for the **BooksJp spider** that scrapes Japanese comic information from books.or.jp.

**Covers:**
- Topic list processing (series names)
- Search results extraction with pagination
- Detail page parsing with multiple author formats
- Release date parsing in Japanese format (YYYY年MM月DD日)
- E-book detection and filtering
- Old release date filtering

**Key features:**
- Multiple test cases for date format handling
- Topic mismatch detection
- WebDriver lifecycle management

### 4. `test_pipelines.py`
Tests for the **ComicScrapersPipeline** that processes scraped items and saves to database.

**Covers:**
- `_get_book_title_tw()` - Parse Taiwanese book titles
- `_get_book_release_date_jp()` - Parse Japanese release dates
- `_get_book_title_jp()` - Parse Japanese book titles
- `_process_orphan_volume_item()` - Handle volumes without series info
- `_process_orphan_map_item()` - Map volumes to series
- `_process_jp_comic_item()` - Process Japanese comic data

**Key features:**
- Database model mocking (Volume, Series, Publisher)
- ISBN validation
- Volume number extraction
- Special edition detection (特裝版, 完)

## Running Tests

### Run Tests in Docker

```bash
# From project root
docker compose exec web python manage.py test comic_scrapers.tests
```

### Run All Tests
```bash
# From project root
cd src
python -m pytest comic_scrapers/tests/

# Or using unittest
python -m unittest discover comic_scrapers/tests/
```

### Run Individual Test Files

**Test BooksTW spider:**
```bash
python -m pytest comic_scrapers/tests/test_books_tw.py -v
```

**Test Eslite spider:**
```bash
python -m pytest comic_scrapers/tests/test_eslite.py -v
```

**Test BooksJp spider:**
```bash
python -m pytest comic_scrapers/tests/test_books_jp.py -v
```

**Test Pipelines:**
```bash
python -m pytest comic_scrapers/tests/test_pipelines.py -v
```

### Run Specific Test Classes or Methods

**Run a specific test class:**
```bash
python -m pytest comic_scrapers/tests/test_books_tw.py::TestBooksTWSpiderParseVolumeInfo -v
```

**Run a specific test method:**
```bash
python -m pytest comic_scrapers/tests/test_eslite.py::TestEsliteSpiderParseSearchResults::test_parse_search_results_extracts_urls -v
```

### Run Tests with Coverage

```bash
# Install coverage if not already installed
pip install pytest-cov

# Run with coverage report
python -m pytest comic_scrapers/tests/ --cov=comic_scrapers --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Structure

Each test file follows this structure:

```python
class TestClassName(unittest.TestCase):
    """Test cases for the specific functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Initialize mocks and test data

    def test_specific_functionality(self):
        """Test that specific_functionality() works correctly."""
        # Arrange
        # Act
        # Assert
```

## Mock Data Formats

### Real Data Examples

**Eslite (map_test2.json):**
- Fields contain newlines: `"作\n者：\n内海ロング"`
- Publisher with full company name: `"出\n版\n社：\n長鴻出版社股份有限公司"`

**BooksJp (jp_titletw.json):**
- Multiple author elements: `["", "少年サンデーコミックス", "原案：牧 彰久", "絵：箭坪 幹"]`
- HTML product description with `<p>`, `<br>` tags

**BooksTW (books_tw.json):**
- Simple ISBN and source URL structure

## Common Issues

### 1. StaleElementReferenceException
**Solution:** Mock tests refresh element lists after processing each item
```python
# Refresh links list after navigating back
links = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, links_xpath)))
```

### 2. Iterator Exhaustion
**Solution:** Use `side_effect` with lambda to return fresh iterators
```python
def mock_parse_detail_info(*args, **kwargs):
    return iter([JpComicItem()])
```

### 3. Selenium Import Issues
**Solution:** Import specific exceptions
```python
from selenium.common.exceptions import TimeoutException, NoSuchElementException
```

## Dependencies

- `scrapy` - Web scraping framework
- `selenium` - Browser automation
- `unittest.mock` - Mocking framework
- `pytest` (optional) - Test runner with better reporting

## Related Files

- **Spiders:** `comic_scrapers/spiders/`
- **Pipelines:** `comic_scrapers/pipelines.py`
- **Items:** `comic_scrapers/items.py`
- **Settings:** `comic_scrapers/settings.py`
