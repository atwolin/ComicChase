"""Unit tests for Celery tasks.

Test Types:
-----------
- **Unit Tests**: Test individual task logic with call_command and database mocked.
  Focus on command invocation, parameter handling, and return values.

Test Execution:
---------------
- All tests use mocked call_command and Django models
- No real spiders are executed
- No real database queries
- Fast execution suitable for CI/CD

Coverage:
---------
- Task execution and return values
- Management command invocation with correct parameters
- Error handling and retry configuration
- Group task creation
- Date formatting and None handling
"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from comic_scrapers.tasks import (
    crawl_all_series_booksjp,
    crawl_all_series_eslite,
    crawl_new_volumes_bookstw,
    crawl_orphan_volumes_eslite,
    crawl_single_isbn_eslite,
    crawl_single_title_booksjp,
    crawl_single_title_eslite,
)


class TestCrawlNewVolumesBookstw(unittest.TestCase):
    """[UNIT] Test crawl_new_volumes_bookstw task."""

    @patch("comic_scrapers.tasks.call_command")
    def test_successful_crawl_returns_completed_status(self, mock_call_command):
        """Test successful execution returns completed status."""
        # Act
        result = crawl_new_volumes_bookstw()

        # Assert
        self.assertEqual(result["status"], "completed")
        self.assertIn("task_id", result)
        self.assertIn("output", result)

    @patch("comic_scrapers.tasks.call_command")
    def test_calls_correct_management_command(self, mock_call_command):
        """Test that correct management command is called."""
        # Act
        crawl_new_volumes_bookstw()

        # Assert
        mock_call_command.assert_called_once()
        # First argument should be the command name
        call_args = mock_call_command.call_args[0]
        self.assertEqual(call_args[0], "books_tw_new_releases")

    @patch("comic_scrapers.tasks.call_command")
    def test_captures_stdout_and_stderr(self, mock_call_command):
        """Test that stdout and stderr are captured."""

        # Arrange
        def write_to_stdout(*args, **kwargs):
            stdout = kwargs.get("stdout")
            if stdout:
                stdout.write("Test output from spider")

        mock_call_command.side_effect = write_to_stdout

        # Act
        crawl_new_volumes_bookstw()

        # Assert
        call_kwargs = mock_call_command.call_args[1]
        self.assertIn("stdout", call_kwargs)
        self.assertIn("stderr", call_kwargs)

    @patch("comic_scrapers.tasks.call_command")
    def test_raises_exception_on_failure(self, mock_call_command):
        """Test that Exception is raised on command failure."""
        # Arrange
        mock_call_command.side_effect = Exception("Command failed")

        # Act & Assert
        with self.assertRaises(Exception):
            crawl_new_volumes_bookstw()


class TestCrawlSingleIsbnEslite(unittest.TestCase):
    """[UNIT] Test crawl_single_isbn_eslite task."""

    @patch("comic_scrapers.tasks.call_command")
    def test_successful_crawl_returns_isbn_in_result(self, mock_call_command):
        """Test that result includes the searched ISBN."""
        # Arrange
        isbn = "9789861238999"

        # Act
        result = crawl_single_isbn_eslite(isbn)

        # Assert
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["isbn"], isbn)
        self.assertIn("task_id", result)

    @patch("comic_scrapers.tasks.call_command")
    def test_calls_correct_management_command(self, mock_call_command):
        """Test that eslite_isbn_search command is called."""
        # Arrange
        isbn = "9789861238999"

        # Act
        crawl_single_isbn_eslite(isbn)

        # Assert
        call_args = mock_call_command.call_args[0]
        self.assertEqual(call_args[0], "eslite_isbn_search")

    @patch("comic_scrapers.tasks.call_command")
    def test_calls_command_with_correct_isbn_parameter(self, mock_call_command):
        """Test that ISBN is passed correctly to the command."""
        # Arrange
        isbn = "9789861238999"

        # Act
        crawl_single_isbn_eslite(isbn)

        # Assert
        call_kwargs = mock_call_command.call_args[1]
        self.assertEqual(call_kwargs["isbn"], isbn)

    @patch("comic_scrapers.tasks.call_command")
    def test_captures_command_output(self, mock_call_command):
        """Test that stdout and stderr are captured."""
        # Act
        crawl_single_isbn_eslite("9789861238999")

        # Assert
        call_kwargs = mock_call_command.call_args[1]
        self.assertIn("stdout", call_kwargs)
        self.assertIn("stderr", call_kwargs)

    @patch("comic_scrapers.tasks.call_command")
    def test_handles_command_exception(self, mock_call_command):
        """Test that exceptions are raised and will be auto-retried."""
        # Arrange
        mock_call_command.side_effect = Exception("Command failed")

        # Act & Assert
        with self.assertRaises(Exception):
            crawl_single_isbn_eslite("9789861238999")


class TestCrawlSingleTitleEslite(unittest.TestCase):
    """[UNIT] Test crawl_single_title_eslite task."""

    @patch("comic_scrapers.tasks.call_command")
    def test_successful_crawl_returns_title_in_result(self, mock_call_command):
        """Test that result includes the searched title."""
        # Arrange
        title = "葬送的芙莉蓮"
        last_release_date = "2025-12-01"

        # Act
        result = crawl_single_title_eslite(title, last_release_date)

        # Assert
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["title"], title)
        self.assertIn("task_id", result)

    @patch("comic_scrapers.tasks.call_command")
    def test_calls_command_with_correct_parameters(self, mock_call_command):
        """Test that command is called with title and last_release_date."""
        # Arrange
        title = "SPY×FAMILY"
        last_release_date = "2025-11-15"

        # Act
        crawl_single_title_eslite(title, last_release_date)

        # Assert
        mock_call_command.assert_called_once()
        call_args = mock_call_command.call_args[0]
        call_kwargs = mock_call_command.call_args[1]

        self.assertEqual(call_args[0], "eslite_title_search")
        self.assertEqual(call_kwargs["title"], title)
        self.assertEqual(call_kwargs["last_release_date"], last_release_date)

    @patch("comic_scrapers.tasks.call_command")
    def test_captures_command_output(self, mock_call_command):
        """Test that stdout and stderr are passed to call_command."""
        # Act
        crawl_single_title_eslite("鏈鋸人", "2025-10-20")

        # Assert
        call_kwargs = mock_call_command.call_args[1]
        self.assertIn("stdout", call_kwargs)
        self.assertIn("stderr", call_kwargs)

    @patch("comic_scrapers.tasks.call_command")
    def test_handles_command_exception(self, mock_call_command):
        """Test that exceptions are raised and will be auto-retried."""
        # Arrange
        mock_call_command.side_effect = Exception("Command failed")

        # Act & Assert
        with self.assertRaises(Exception):
            crawl_single_title_eslite("test", "2025-12-01")


class TestCrawlSingleTitleBooksjp(unittest.TestCase):
    """[UNIT] Test crawl_single_title_booksjp task."""

    @patch("comic_scrapers.tasks.call_command")
    def test_successful_crawl_returns_correct_result(self, mock_call_command):
        """Test successful execution for Japanese title."""
        # Arrange
        title = "葬送のフリーレン"
        last_release_date = "2025-12-01"

        # Act
        result = crawl_single_title_booksjp(title, last_release_date)

        # Assert
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["title"], title)

    @patch("comic_scrapers.tasks.call_command")
    def test_calls_correct_management_command(self, mock_call_command):
        """Test that books_jp_title_search command is called."""
        # Act
        crawl_single_title_booksjp("test", "2025-12-01")

        # Assert
        call_args = mock_call_command.call_args[0]
        self.assertEqual(call_args[0], "books_jp_title_search")

    @patch("comic_scrapers.tasks.call_command")
    def test_includes_parameters_in_call(self, mock_call_command):
        """Test that title and last_release_date are passed correctly."""
        # Arrange
        title = "test_title"
        last_date = "2025-11-20"

        # Act
        crawl_single_title_booksjp(title, last_date)

        # Assert
        call_kwargs = mock_call_command.call_args[1]
        self.assertEqual(call_kwargs["title"], title)
        self.assertEqual(call_kwargs["last_release_date"], last_date)


class TestCrawlOrphanVolumesEslite(unittest.TestCase):
    """[UNIT] Test crawl_orphan_volumes_eslite task."""

    @patch("comic_scrapers.tasks.crawl_single_isbn_eslite")
    @patch("comic.models.Volume")
    def test_creates_task_for_each_orphan_volume(self, mock_volume, mock_crawl_task):
        """Test that a task is created for each orphan volume with ISBN."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values_list.return_value = [
            "9789861238999",
            "9784065123456",
            "9784088123456",
        ]
        mock_volume.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        result = crawl_orphan_volumes_eslite()

        # Assert
        self.assertEqual(result["total_tasks"], 3)
        # Verify chunks was called with correct ISBN tuples and chunk size
        mock_crawl_task.chunks.assert_called_once()
        call_args = mock_crawl_task.chunks.call_args[0]
        self.assertEqual(len(call_args[0]), 3)  # 3 ISBNs
        self.assertEqual(call_args[1], 20)  # chunk size

    @patch("comic_scrapers.tasks.crawl_single_isbn_eslite")
    @patch("comic.models.Volume")
    def test_queries_only_orphan_volumes_with_isbn(self, mock_volume, mock_crawl_task):
        """Test that query filters for orphan volumes (no series) with ISBN."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values_list.return_value = []
        mock_volume.objects.filter.return_value = mock_queryset

        # Act
        crawl_orphan_volumes_eslite()

        # Assert
        mock_volume.objects.filter.assert_called_once_with(
            series__isnull=True, isbn__isnull=False
        )

    @patch("comic_scrapers.tasks.crawl_single_isbn_eslite")
    @patch("comic.models.Volume")
    def test_passes_isbn_to_single_task(self, mock_volume, mock_crawl_task):
        """Test that ISBNs are passed correctly to chunks."""
        # Arrange
        test_isbn = "9789861238999"
        mock_queryset = MagicMock()
        mock_queryset.values_list.return_value = [test_isbn]
        mock_volume.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        crawl_orphan_volumes_eslite()

        # Assert
        mock_crawl_task.chunks.assert_called_once()
        call_args = mock_crawl_task.chunks.call_args[0]
        # Check that the ISBN is in the list of tuples
        self.assertEqual(call_args[0], [(test_isbn,)])

    @patch("comic_scrapers.tasks.crawl_single_isbn_eslite")
    @patch("comic.models.Volume")
    def test_returns_zero_tasks_when_no_orphan_volumes(
        self, mock_volume, mock_crawl_task
    ):
        """Test behavior when no orphan volumes with ISBN exist."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values_list.return_value = []
        mock_volume.objects.filter.return_value = mock_queryset

        # Act
        result = crawl_orphan_volumes_eslite()

        # Assert
        self.assertEqual(result["total_tasks"], 0)
        mock_crawl_task.chunks.assert_not_called()


class TestCrawlAllSeriesEslite(unittest.TestCase):
    """[UNIT] Test crawl_all_series_eslite task."""

    @patch("comic_scrapers.tasks.crawl_single_title_eslite")
    @patch("comic.models.Series")
    def test_creates_task_for_each_series(self, mock_series, mock_crawl_task):
        """Test that a task is created for each series with TC title."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = [
            {"title_tw": "葬送的芙莉蓮", "latest_volume_tw__release_date": None},
            {"title_tw": "SPY×FAMILY", "latest_volume_tw__release_date": None},
            {"title_tw": "鏈鋸人", "latest_volume_tw__release_date": None},
        ]
        mock_series.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        result = crawl_all_series_eslite()

        # Assert
        self.assertEqual(result["total_tasks"], 3)
        # Verify chunks was called with correct arguments and chunk size
        mock_crawl_task.chunks.assert_called_once()
        call_args = mock_crawl_task.chunks.call_args[0]
        self.assertEqual(len(call_args[0]), 3)  # 3 series
        self.assertEqual(call_args[1], 20)  # chunk size

    @patch("comic_scrapers.tasks.crawl_single_title_eslite")
    @patch("comic.models.Series")
    def test_formats_release_date_correctly(self, mock_series, mock_crawl_task):
        """Test that release date is formatted to YYYY-MM-DD string."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = [
            {
                "title_tw": "葬送的芙莉蓮",
                "latest_volume_tw__release_date": date(2025, 12, 1),
            },
        ]
        mock_series.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        crawl_all_series_eslite()

        # Assert
        # Verify the task arguments contain formatted date
        call_args = mock_crawl_task.chunks.call_args[0]
        task_args = call_args[0]
        self.assertEqual(task_args[0], ("葬送的芙莉蓮", "2025-12-01"))

    @patch("comic_scrapers.tasks.crawl_single_title_eslite")
    @patch("comic.models.Series")
    def test_handles_none_release_date(self, mock_series, mock_crawl_task):
        """Test that None release date is passed as None."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = [
            {"title_tw": "Test", "latest_volume_tw__release_date": None},
        ]
        mock_series.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        crawl_all_series_eslite()

        # Assert
        call_args = mock_crawl_task.chunks.call_args[0]
        task_args = call_args[0]
        self.assertEqual(task_args[0], ("Test", None))

    @patch("comic_scrapers.tasks.crawl_single_title_eslite")
    @patch("comic.models.Series")
    def test_returns_zero_tasks_when_no_series(self, mock_series, mock_crawl_task):
        """Test behavior when no series with Traditional Chinese titles exist."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = []
        mock_series.objects.filter.return_value = mock_queryset

        # Act
        result = crawl_all_series_eslite()

        # Assert
        self.assertEqual(result["total_tasks"], 0)
        self.assertIsNone(result["group_id"])
        mock_crawl_task.chunks.assert_not_called()

    @patch("comic_scrapers.tasks.crawl_single_title_eslite")
    @patch("comic.models.Series")
    def test_queries_only_series_with_traditional_chinese_titles(
        self, mock_series, mock_crawl_task
    ):
        """Test that query filters for non-null title_tw."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = []
        mock_series.objects.filter.return_value = mock_queryset

        # Act
        crawl_all_series_eslite()

        # Assert
        mock_series.objects.filter.assert_called_once_with(title_tw__isnull=False)


class TestCrawlAllSeriesBooksjp(unittest.TestCase):
    """[UNIT] Test crawl_all_series_booksjp task."""

    @patch("comic_scrapers.tasks.crawl_single_title_booksjp")
    @patch("comic.models.Series")
    def test_creates_task_for_each_japanese_series(self, mock_series, mock_crawl_task):
        """Test that a task is created for each series with Japanese title."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = [
            {"title_jp": "葬送のフリーレン", "latest_volume_jp__release_date": None},
            {"title_jp": "ブルーピリオド", "latest_volume_jp__release_date": None},
        ]
        mock_series.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        result = crawl_all_series_booksjp()

        # Assert
        self.assertEqual(result["total_tasks"], 2)
        # Verify chunks was called with correct arguments and chunk size
        mock_crawl_task.chunks.assert_called_once()
        call_args = mock_crawl_task.chunks.call_args[0]
        self.assertEqual(len(call_args[0]), 2)  # 2 series
        self.assertEqual(call_args[1], 20)  # chunk size

    @patch("comic_scrapers.tasks.crawl_single_title_booksjp")
    @patch("comic.models.Series")
    def test_queries_only_series_with_japanese_titles(
        self, mock_series, mock_crawl_task
    ):
        """Test that query filters for non-null title_jp."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = []
        mock_series.objects.filter.return_value = mock_queryset

        # Act
        crawl_all_series_booksjp()

        # Assert
        mock_series.objects.filter.assert_called_once_with(title_jp__isnull=False)

    @patch("comic_scrapers.tasks.crawl_single_title_booksjp")
    @patch("comic.models.Series")
    def test_formats_japanese_release_date(self, mock_series, mock_crawl_task):
        """Test that Japanese release date is formatted correctly."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = [
            {
                "title_jp": "ブルーピリオド",
                "latest_volume_jp__release_date": date(2025, 11, 20),
            },
        ]
        mock_series.objects.filter.return_value = mock_queryset

        # Mock the chunks method
        mock_chunks_result = MagicMock()
        mock_chunks_result.apply_async.return_value = MagicMock(id="test-group-id")
        mock_crawl_task.chunks.return_value = mock_chunks_result

        # Act
        crawl_all_series_booksjp()

        # Assert
        call_args = mock_crawl_task.chunks.call_args[0]
        task_args = call_args[0]
        self.assertEqual(task_args[0], ("ブルーピリオド", "2025-11-20"))

    @patch("comic_scrapers.tasks.crawl_single_title_booksjp")
    @patch("comic.models.Series")
    def test_returns_zero_tasks_when_no_series(self, mock_series, mock_crawl_task):
        """Test behavior when no series with Japanese titles exist."""
        # Arrange
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = []
        mock_series.objects.filter.return_value = mock_queryset

        # Act
        result = crawl_all_series_booksjp()

        # Assert
        self.assertEqual(result["total_tasks"], 0)
        self.assertIsNone(result["group_id"])
        mock_crawl_task.chunks.assert_not_called()


class TestTaskConfiguration(unittest.TestCase):
    """[UNIT] Test Celery task configuration."""

    def test_crawl_new_volumes_bookstw_has_correct_retry_config(self):
        """Test retry configuration for crawl_new_volumes_bookstw."""
        task = crawl_new_volumes_bookstw

        self.assertEqual(task.max_retries, 3)
        self.assertTrue(task.acks_late)
        self.assertIn(Exception, task.autoretry_for)
        self.assertEqual(task.retry_backoff, 60 * 10)
        self.assertEqual(task.retry_backoff_max, 60 * 20)
        self.assertTrue(task.retry_jitter)

    def test_crawl_single_title_eslite_has_correct_config(self):
        """Test configuration for crawl_single_title_eslite."""
        task = crawl_single_title_eslite

        self.assertEqual(task.soft_time_limit, 2400)
        self.assertEqual(task.time_limit, 3000)
        self.assertEqual(task.max_retries, 3)
        self.assertTrue(task.acks_late)
        self.assertIn(Exception, task.autoretry_for)
        self.assertEqual(task.retry_backoff, 60 * 5)
        self.assertEqual(task.retry_backoff_max, 60 * 20)

    def test_crawl_single_title_booksjp_has_correct_config(self):
        """Test configuration for crawl_single_title_booksjp."""
        task = crawl_single_title_booksjp

        self.assertEqual(task.soft_time_limit, 2400)
        self.assertEqual(task.time_limit, 3000)
        self.assertIn(Exception, task.autoretry_for)
        self.assertTrue(task.retry_jitter)

    def test_crawl_single_isbn_eslite_has_correct_config(self):
        """Test configuration for crawl_single_isbn_eslite."""
        task = crawl_single_isbn_eslite

        self.assertEqual(task.soft_time_limit, 2400)
        self.assertEqual(task.time_limit, 3000)
        self.assertEqual(task.max_retries, 3)
        self.assertTrue(task.acks_late)
        self.assertIn(Exception, task.autoretry_for)
        self.assertEqual(task.retry_backoff, 60 * 5)
        self.assertEqual(task.retry_backoff_max, 60 * 20)

    def test_all_tasks_have_correct_names(self):
        """Test that task names are correctly set."""
        self.assertEqual(
            crawl_new_volumes_bookstw.name,
            "comic_scrapers.tasks.crawl_new_volumes_bookstw",
        )
        self.assertEqual(
            crawl_single_isbn_eslite.name,
            "comic_scrapers.tasks.crawl_single_isbn_eslite",
        )
        self.assertEqual(
            crawl_single_title_eslite.name,
            "comic_scrapers.tasks.crawl_single_title_eslite",
        )
        self.assertEqual(
            crawl_single_title_booksjp.name,
            "comic_scrapers.tasks.crawl_single_title_booksjp",
        )
        self.assertEqual(
            crawl_orphan_volumes_eslite.name,
            "comic_scrapers.tasks.crawl_orphan_volumes_eslite",
        )
        self.assertEqual(
            crawl_all_series_eslite.name, "comic_scrapers.tasks.crawl_all_series_eslite"
        )
        self.assertEqual(
            crawl_all_series_booksjp.name,
            "comic_scrapers.tasks.crawl_all_series_booksjp",
        )


if __name__ == "__main__":
    unittest.main()
