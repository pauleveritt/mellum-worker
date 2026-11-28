"""Retrying flaky calls."""
import time


def retry(fn, *, attempts=3, base_delay=0.1, factor=2.0, retry_on=(Exception,), sleep=time.sleep):
    last = None
    for n in range(attempts):
        try:
            return fn()
        except retry_on as exc:
            last = exc
            sleep(base_delay * factor ** n)
    raise last
