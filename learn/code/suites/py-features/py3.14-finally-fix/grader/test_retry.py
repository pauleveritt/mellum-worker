from retry import fetch_with_retry


def test_first_success_is_returned_and_logged_once():
    calls, logs = iter([OSError, "ok"]), []

    def fetch():
        value = next(calls)
        if value is OSError:
            raise OSError
        return value
    assert fetch_with_retry(fetch, logs.append) == "ok"
    assert logs == ["done"]


def test_all_failures_return_none_and_log_once():
    logs = []

    def fetch():
        raise OSError
    assert fetch_with_retry(fetch, logs.append, attempts=2) is None
    assert logs == ["done"]
