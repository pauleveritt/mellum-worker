import pytest

from config import load

TEXT = "# app\nname=demo\n\nmode=fast\n"


def test_mapping_contents():
    assert dict(load(TEXT)) == {"name": "demo", "mode": "fast"}


def test_immutable_and_hashable():
    cfg = load(TEXT)
    with pytest.raises(TypeError):
        cfg["name"] = "other"
    assert {cfg: 1}[load(TEXT)] == 1
