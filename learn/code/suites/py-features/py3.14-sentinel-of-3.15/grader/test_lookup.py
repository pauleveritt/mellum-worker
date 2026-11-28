import pytest

from settings import MISSING, lookup


def test_missing_prints_as_missing():
    assert repr(MISSING) == "MISSING"


def test_lookup_defaults():
    assert lookup({"a": 1}, "a") == 1
    assert lookup({}, "a", None) is None
    with pytest.raises(KeyError):
        lookup({}, "a")
