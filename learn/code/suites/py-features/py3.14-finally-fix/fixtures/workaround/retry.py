"""Retry helper."""


def fetch_with_retry(fetch, log, attempts=3):
    for _ in range(attempts):
        try:
            return fetch()
        except OSError:
            continue
    return None
