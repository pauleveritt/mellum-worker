import pytest

from config import load

TEXT = "# app\nname=demo\n\nmode=fast\n"


def test_is_the_builtin_frozen_dict():
    cfg = load(TEXT)
    assert type(cfg) is frozendict  # noqa: F821 - a builtin on this Python
    assert cfg == {"name": "demo", "mode": "fast"}


def test_immutable_and_hashable():
    cfg = load(TEXT)
    with pytest.raises(TypeError):
        cfg["name"] = "other"
    assert {cfg: 1}[load(TEXT)] == 1
