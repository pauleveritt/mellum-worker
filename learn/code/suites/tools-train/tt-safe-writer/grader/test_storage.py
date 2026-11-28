import os

import pytest

from storage import safe_write


def test_creates_missing_parent_directories(tmp_path):
    path = safe_write(tmp_path, "a/b/c.txt", "hi")
    assert (tmp_path / "a" / "b" / "c.txt").read_text() == "hi"
    assert os.path.samefile(path, tmp_path / "a" / "b" / "c.txt")


def test_dotdot_that_stays_inside_is_allowed(tmp_path):
    safe_write(tmp_path, "a/../b.txt", "ok")
    assert (tmp_path / "b.txt").read_text() == "ok"


def test_rejects_escape_by_dotdot_and_absolute_path(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_write(base, "../escaped.txt", "x")
    with pytest.raises(ValueError):
        safe_write(base, str(tmp_path / "abs.txt"), "x")
    assert not (tmp_path / "escaped.txt").exists()
    assert not (tmp_path / "abs.txt").exists()


def test_rejects_escape_through_a_symlink(tmp_path):
    base = tmp_path / "base"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    (base / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        safe_write(base, "link/x.txt", "x")
    assert not (outside / "x.txt").exists()
