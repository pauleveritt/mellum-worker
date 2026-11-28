import pytest

import fetcher
from retry import retry


class Flaky:
    def __init__(self, failures, error=ConnectionError):
        self.failures, self.error, self.calls = failures, error, 0

    def read(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error(f"fail {self.calls}")
        return "data"


def test_succeeds_after_failures_with_growing_delays():
    delays = []
    src = Flaky(2)
    assert retry(src.read, sleep=delays.append) == "data"
    assert delays == pytest.approx([0.1, 0.2])


def test_gives_up_and_reraises_last_error_without_final_sleep():
    delays = []
    src = Flaky(10)
    with pytest.raises(ConnectionError, match="fail 3"):
        retry(src.read, attempts=3, sleep=delays.append)
    assert src.calls == 3
    assert delays == pytest.approx([0.1, 0.2])


def test_other_errors_are_not_retried():
    delays = []
    src = Flaky(1, error=KeyError)
    with pytest.raises(KeyError):
        retry(src.read, retry_on=(ConnectionError,), sleep=delays.append)
    assert src.calls == 1
    assert delays == []


def test_fetcher_uses_its_own_schedule():
    delays = []
    src = Flaky(3)
    assert fetcher.load(src, sleep=delays.append) == "data"
    assert delays == pytest.approx([0.5, 1.0, 2.0])
