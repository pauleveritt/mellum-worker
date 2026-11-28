"""Retry helper."""


def fetch_with_retry(fetch, log, attempts=3):
    result = None
    try:
        for _ in range(attempts):
            try:
                result = fetch()
                break
            except OSError:
                continue
        return result
    finally:
        log("done")
