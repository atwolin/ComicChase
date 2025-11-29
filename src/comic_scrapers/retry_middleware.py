"""Custom retry middleware for handling HTTP 484 errors with backoff."""

import time

from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class Custom484RetryMiddleware(RetryMiddleware):
    """Custom retry middleware that handles HTTP 484 status codes.

    This middleware extends the default RetryMiddleware to specifically handle
    HTTP 484 errors (rate limiting) by sleeping before retrying the request.
    """

    def process_response(self, request, response, spider):
        """Process the response and retry if status code is 484.

        Args:
            request: The request that resulted in this response
            response: The HTTP response object
            spider: The spider making the request

        Returns:
            Either the original response or a new retry request
        """
        if response.status == 484:
            reason = response_status_message(response.status)
            retry_times = request.meta.get("retry_times", 0) + 1
            max_retry_times = self.max_retry_times

            if retry_times <= max_retry_times:
                # Calculate sleep time with exponential backoff
                # First retry: 30s, second: 60s, third: 120s, etc.
                sleep_time = 30 * (2 ** (retry_times - 1))

                spider.logger.warning(
                    f"Received HTTP 484 from {request.url}. "
                    f"Sleeping for {sleep_time} seconds before retry "
                    f"(attempt {retry_times}/{max_retry_times})"
                )

                time.sleep(sleep_time)

                retryreq = request.copy()
                retryreq.meta["retry_times"] = retry_times
                retryreq.dont_filter = True

                return retryreq
            else:
                spider.logger.error(
                    f"Gave up retrying {request.url} after {retry_times} attempts "
                    f"(HTTP 484: {reason})"
                )

        # For all other status codes, use the default behavior
        return super().process_response(request, response, spider)
