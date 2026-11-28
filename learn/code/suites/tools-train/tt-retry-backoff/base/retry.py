"""Retrying flaky calls."""
import time


def retry(fn, *, attempts=3, base_delay=0.1, factor=2.0, retry_on=(Exception,), sleep=time.sleep):
    raise NotImplementedError
