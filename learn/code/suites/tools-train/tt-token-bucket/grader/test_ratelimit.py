import pytest

from client import ApiClient, RateLimited
from ratelimit import TokenBucket


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_starts_full_then_refuses():
    bucket = TokenBucket(rate=1, capacity=3, clock=Clock())
    assert [bucket.try_acquire() for _ in range(4)] == [True, True, True, False]


def test_refills_with_time_but_never_above_capacity():
    clock = Clock()
    bucket = TokenBucket(rate=2, capacity=3, clock=clock)
    for _ in range(3):
        bucket.try_acquire()
    clock.now += 0.5
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    clock.now += 100
    assert [bucket.try_acquire() for _ in range(4)] == [True, True, True, False]


def test_refused_request_takes_nothing():
    bucket = TokenBucket(rate=1, capacity=2, clock=Clock())
    assert bucket.try_acquire(3) is False
    assert bucket.try_acquire(2) is True


def test_client_refuses_without_calling_transport():
    seen = []
    clock = Clock()
    api = ApiClient(lambda p: seen.append(p) or "ok", TokenBucket(rate=1, capacity=1, clock=clock))
    assert api.get("/a") == "ok"
    with pytest.raises(RateLimited):
        api.get("/b")
    assert seen == ["/a"]
    clock.now += 1
    assert api.get("/c") == "ok"
