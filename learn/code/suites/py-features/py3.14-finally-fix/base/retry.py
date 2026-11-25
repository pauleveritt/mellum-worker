"""Retry helper."""


def fetch_with_retry(fetch, log, attempts=3):
    result = None
    for _ in range(attempts):
        try:
            result = fetch()
            break
        except OSError:
            continue
        finally:
            if result is not None:
                return result
    try:
        return result
    finally:
        log("done")
        return result
