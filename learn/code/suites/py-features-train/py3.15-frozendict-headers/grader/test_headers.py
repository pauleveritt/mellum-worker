import pytest

from headers import parse

RAW = "Content-Type: text/html\n\nX-Request-Id:  abc123 \n"


def test_is_the_builtin_frozen_dict():
    h = parse(RAW)
    assert type(h) is frozendict  # noqa: F821 - a builtin on this Python
    assert h == {"content-type": "text/html", "x-request-id": "abc123"}


def test_immutable_and_hashable():
    h = parse(RAW)
    with pytest.raises(TypeError):
        h["content-type"] = "x"
    assert len({parse(RAW), parse(RAW)}) == 1
