"""Memoising helpers."""
from collections import OrderedDict
from functools import wraps


def cached(maxsize=128):
    """Remember results by arguments, keeping at most `maxsize` entries (least recently used goes first)."""
    def decorate(fn):
        store = OrderedDict()

        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key in store:
                store.move_to_end(key)
                return store[key]
            value = fn(*args, **kwargs)
            store[key] = value
            if len(store) > maxsize:
                store.popitem(last=False)
            return value

        wrapper.cache_clear = store.clear
        return wrapper
    return decorate
