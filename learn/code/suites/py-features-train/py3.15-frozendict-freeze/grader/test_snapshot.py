from snapshot import freeze

STATE = {"user": {"name": "ada", "roles": ["admin", "dev"]}, "count": 2}


def test_dicts_become_the_builtin_frozen_dict_at_every_depth():
    s = freeze(STATE)
    assert type(s) is frozendict and type(s["user"]) is frozendict  # noqa: F821 - builtins on this Python
    assert s["user"]["roles"] == ("admin", "dev") and s["count"] == 2


def test_snapshots_are_hashable_and_equal():
    assert len({freeze(STATE), freeze(STATE)}) == 1
