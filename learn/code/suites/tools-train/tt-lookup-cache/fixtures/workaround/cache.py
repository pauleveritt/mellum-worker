"""Memoising helpers."""
from functools import wraps


def cached(maxsize=128):
    def decorate(fn):
        store = {}

        @wraps(fn)
        def wrapper(*args):
            if args in store:
                return store[args]
            value = fn(*args)
            store[args] = value
            if len(store) > maxsize:
                del store[next(iter(store))]  # drops the oldest insert, not the least recently used
            return value

        wrapper.cache_clear = store.clear
        return wrapper
    return decorate
