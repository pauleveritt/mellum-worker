"""Retrying flaky calls."""
import time


def retry(fn, *, attempts=3, base_delay=0.1, factor=2.0, retry_on=(Exception,), sleep=time.sleep):
    """Call fn() up to `attempts` times, backing off exponentially between retryable failures."""
    for n in range(attempts):
        try:
            return fn()
        except retry_on:
            if n == attempts - 1:
                raise
            sleep(base_delay * factor ** n)
