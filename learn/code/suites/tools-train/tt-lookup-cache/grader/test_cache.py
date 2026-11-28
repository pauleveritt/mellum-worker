import backend
import catalog
from cache import cached


def counting():
    calls = []

    def square(x):
        calls.append(x)
        return x * x
    return calls, square


def test_fetch_price_hits_backend_once_per_sku():
    catalog.fetch_price.cache_clear()
    backend.CALLS.clear()
    assert catalog.basket_total(["A", "B", "A", "A", "B"]) == 80
    assert sorted(backend.CALLS) == ["A", "B"]


def test_evicts_least_recently_used():
    calls, square = counting()
    f = cached(maxsize=2)(square)
    f(1); f(2); f(1); f(3)
    calls.clear()
    assert f(1) == 1
    assert calls == []
    assert f(2) == 4
    assert calls == [2]


def test_cache_clear_forgets_everything():
    calls, square = counting()
    f = cached(maxsize=4)(square)
    f(5); f(5)
    f.cache_clear()
    f(5)
    assert calls == [5, 5]
