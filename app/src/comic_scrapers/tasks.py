import logging
from io import StringIO

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=10 * 60,
    retry_backoff_max=20 * 60,
    retry_jitter=True,
)
def crawl_new_volumes_bookstw(self):
    """Crawl new book releases from books.com.tw."""
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting new volumes crawl from books.com.tw")

    # Capture command output
    out = StringIO()
    err = StringIO()

    try:
        call_command("books_tw_new_releases", stdout=out, stderr=err)

        stdout_content = out.getvalue()
        stderr_content = err.getvalue()

        # Log full output for debugging
        if stdout_content:
            logger.info(f"[{task_id}] Command stdout: {stdout_content}")
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")

        logger.info(f"[{task_id}] Completed new volumes crawl")

        return {
            "task_id": task_id,
            "status": "completed",
            "output": stdout_content[-500:] if stdout_content else "",
            "errors": stderr_content[-500:] if stderr_content else "",
        }
    except Exception:
        stderr_content = err.getvalue()
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")
        logger.exception(f"[{task_id}] Crawl failed")
        raise


@shared_task(
    bind=True,
    soft_time_limit=40 * 60,
    time_limit=50 * 60,
    max_retries=3,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=5 * 60,
    retry_backoff_max=20 * 60,
    retry_jitter=True,
)
def crawl_single_isbn_eslite(self, isbn):
    """Crawl eslite.com using ISBN to map orphan volumes."""
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting eslite.com ISBN crawl for: {isbn}")

    # Capture command output
    out = StringIO()
    err = StringIO()

    try:
        call_command("eslite_isbn_search", isbn=isbn, stdout=out, stderr=err)

        stdout_content = out.getvalue()
        stderr_content = err.getvalue()

        # Log full output for debugging
        if stdout_content:
            logger.info(f"[{task_id}] Command stdout: {stdout_content}")
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")

        logger.info(f"[{task_id}] Completed eslite.com ISBN crawl for: {isbn}")

        return {
            "task_id": task_id,
            "isbn": isbn,
            "status": "completed",
            "output": stdout_content[-500:] if stdout_content else "",
            "errors": stderr_content[-500:] if stderr_content else "",
        }
    except Exception:
        stderr_content = err.getvalue()
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")
        logger.exception(f"[{task_id}] Crawl failed")
        raise


@shared_task(
    bind=True,
    soft_time_limit=40 * 60,
    time_limit=50 * 60,
    max_retries=3,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=5 * 60,
    retry_backoff_max=20 * 60,
    retry_jitter=True,
)
def crawl_single_title_eslite(self, title, last_release_date):
    """Crawl a single comic title in Traditional Chinese from Eslite bookstore.

    Args:
        title (str): Comic title in Traditional Chinese to search for
        last_release_date (str): Last known release date in YYYY-MM-DD format

    Returns:
        dict: Summary of crawl results
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting Eslite crawl for: {title}")

    out = StringIO()
    err = StringIO()

    try:
        call_command(
            "eslite_title_search",
            title=title,
            last_release_date=last_release_date,
            stdout=out,
            stderr=err,
        )

        stdout_content = out.getvalue()
        stderr_content = err.getvalue()

        # Log full output for debugging
        if stdout_content:
            logger.info(f"[{task_id}] Command stdout: {stdout_content}")
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")

        logger.info(f"[{task_id}] Completed crawl for: {title}")

        return {
            "task_id": task_id,
            "title": title,
            "status": "completed",
            "output": stdout_content[-500:] if stdout_content else "",
            "errors": stderr_content[-500:] if stderr_content else "",
        }
    except Exception:
        stderr_content = err.getvalue()
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")
        logger.exception(f"[{task_id}] Crawl failed")
        raise


@shared_task(
    bind=True,
    soft_time_limit=40 * 60,
    time_limit=50 * 60,
    max_retries=3,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=5 * 60,
    retry_backoff_max=20 * 60,
    retry_jitter=True,
)
def crawl_single_title_booksjp(self, title, last_release_date):
    """Crawl a single comic title in Japanese from Books.or.jp.

    Args:
        title (str): Comic title in Japanese to search for
        last_release_date (str): Last known release date in YYYY-MM-DD format

    Returns:
        dict: Summary of crawl results
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting BooksJP crawl for: {title}")

    out = StringIO()
    err = StringIO()

    try:
        call_command(
            "books_jp_title_search",
            title=title,
            last_release_date=last_release_date,
            stdout=out,
            stderr=err,
        )

        stdout_content = out.getvalue()
        stderr_content = err.getvalue()

        # Log full output for debugging
        if stdout_content:
            logger.info(f"[{task_id}] Command stdout: {stdout_content}")
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")

        logger.info(f"[{task_id}] Completed crawl for: {title}")

        return {
            "task_id": task_id,
            "title": title,
            "status": "completed",
            "output": stdout_content[-500:] if stdout_content else "",
            "errors": stderr_content[-500:] if stderr_content else "",
        }
    except Exception:
        stderr_content = err.getvalue()
        if stderr_content:
            logger.warning(f"[{task_id}] Command stderr: {stderr_content}")
        logger.exception(f"[{task_id}] Crawl failed")
        raise


@shared_task(acks_late=True)
def crawl_orphan_volumes_eslite():
    """Schedule crawl tasks for all orphan volumes using ISBN."""
    from comic.models import Volume

    # Query all orphan volumes with ISBN
    orphan_isbns = Volume.objects.filter(
        series__isnull=True, isbn__isnull=False
    ).values_list("isbn", flat=True)

    if not orphan_isbns:
        logger.info("No orphan volumes found for Eslite ISBN crawl")
        return {"total_tasks": 0, "group_id": None}

    # Process in chunks of 20
    chunck_size = 20
    result = crawl_single_isbn_eslite.chunks(
        [(isbn,) for isbn in orphan_isbns], chunck_size
    ).apply_async()  # pyright: ignore[reportCallIssue]

    logger.info(f"Scheduled {len(orphan_isbns)} Eslite ISBN crawl tasks in chunks")
    return {"total_tasks": len(orphan_isbns), "group_id": result.id}


@shared_task(acks_late=True)
def crawl_all_series_eslite():
    """Schedule crawl tasks for all Eslite Traditional Chinese series."""
    from celery import group
    from comic.models import Series

    # Query all series with Traditional Chinese titles
    series_list = Series.objects.filter(title_tw__isnull=False).values(
        "title_tw", "latest_volume_tw__release_date"
    )

    # Create task for each series
    tasks = []
    for series in series_list:
        title = series["title_tw"]
        last_date = series["latest_volume_tw__release_date"]
        last_date_str = last_date.strftime("%Y-%m-%d") if last_date else None

        task = crawl_single_title_eslite.s(title, last_date_str)  # pyright: ignore[reportCallIssue]
        tasks.append(task)

    # Execute tasks in parallel using group
    job = group(tasks)
    result = job.apply_async()  # pyright: ignore[reportCallIssue]

    logger.info(f"Scheduled {len(tasks)} Eslite crawl tasks")

    return {"total_tasks": len(tasks), "group_id": result.id}


@shared_task(acks_late=True)
def crawl_all_series_booksjp():
    """Schedule crawl tasks for all Japanese comic series."""
    from celery import group
    from comic.models import Series

    # Query all series with Japanese titles
    series_list = Series.objects.filter(title_jp__isnull=False).values(
        "title_jp", "latest_volume_jp__release_date"
    )

    tasks = []
    for series in series_list:
        title = series["title_jp"]
        last_date = series["latest_volume_jp__release_date"]
        last_date_str = last_date.strftime("%Y-%m-%d") if last_date else None

        task = crawl_single_title_booksjp.s(title, last_date_str)  # pyright: ignore[reportCallIssue]
        tasks.append(task)

    job = group(tasks)
    result = job.apply_async()  # pyright: ignore[reportCallIssue]

    logger.info(f"Scheduled {len(tasks)} BooksJP crawl tasks")

    return {"total_tasks": len(tasks), "group_id": result.id}
