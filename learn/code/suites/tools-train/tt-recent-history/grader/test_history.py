import pytest

import shell
from history import History


def test_newest_first_with_dedupe():
    h = History(5)
    for item in ["a", "b", "c", "a"]:
        h.add(item)
    assert h.recent() == ["a", "c", "b"]
    assert h.recent(2) == ["a", "c"]


def test_capacity_drops_oldest_and_readd_at_full_keeps_everyone():
    h = History(3)
    for item in ["a", "b", "c", "d"]:
        h.add(item)
    assert h.recent() == ["d", "c", "b"]
    h.add("c")
    assert h.recent() == ["c", "d", "b"]


def test_recent_is_a_copy_and_capacity_is_checked():
    h = History(2)
    h.add("x")
    h.recent().append("junk")
    assert h.recent() == ["x"]
    with pytest.raises(ValueError):
        History(0)


def test_shell_last_command():
    h = History(3)
    shell.run(["ls", "  ", "pwd ", "ls"], h)
    assert shell.last_command(h) == "ls"
    assert shell.last_command(History()) is None
