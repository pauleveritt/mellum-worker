import pytest

from loader import load

SCHEMA = {"job": {"retries": int, "verbose": bool, "quiet": bool, "dry": bool, "tags": list, "empty": list}}


def write(tmp_path, text):
    path = tmp_path / "settings.ini"
    path.write_text(text)
    return path


def test_ints_bools_and_lists_are_typed(tmp_path):
    path = write(tmp_path, "[job]\nretries = 5\nverbose = Yes\nquiet = off\ndry = 1\n"
                           "tags = a , b,c ,\nempty =\nowner = sam\n")
    assert load(path, SCHEMA) == {"job": {"retries": 5, "verbose": True, "quiet": False, "dry": True,
                                          "tags": ["a", "b", "c"], "empty": [], "owner": "sam"}}


def test_invalid_boolean_raises(tmp_path):
    with pytest.raises(ValueError):
        load(write(tmp_path, "[job]\nverbose = maybe\n"), SCHEMA)


def test_default_schema_from_schema_module(tmp_path):
    path = write(tmp_path, "[cache]\nenabled = ON\nttl = 60\nbackends = redis, memory\n")
    assert load(path) == {"cache": {"enabled": True, "ttl": 60, "backends": ["redis", "memory"]}}
