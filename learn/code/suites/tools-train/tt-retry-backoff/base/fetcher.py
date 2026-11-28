"""Reads a remote source, riding out dropped connections."""
import time

from retry import retry


def load(source, sleep=time.sleep):
    return retry(source.read, attempts=4, base_delay=0.5, retry_on=(ConnectionError,), sleep=sleep)
