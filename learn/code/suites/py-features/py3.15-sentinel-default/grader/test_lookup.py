import pytest

from settings import MISSING, lookup


def test_missing_is_a_builtin_sentinel():
    assert repr(MISSING) == "MISSING"
    assert type(MISSING) is type(sentinel("OTHER"))  # noqa: F821 - a builtin on this Python


def test_lookup_defaults():
    assert lookup({"a": 1}, "a") == 1
    assert lookup({}, "a", None) is None
    with pytest.raises(KeyError):
        lookup({}, "a")
