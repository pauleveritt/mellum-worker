import json

import pytest

import loader
from config import ConfigError, ServerConfig


def test_valid_dict_with_defaults(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"host": "db", "port": 5432}))
    cfg = loader.load(p)
    assert cfg == ServerConfig("db", 5432, False, [])
    assert issubclass(ConfigError, ValueError)


def test_wrong_types_name_the_field():
    cases = [
        ({"host": "db", "port": "5432"}, "port"),
        ({"host": "db", "port": True}, "port"),
        ({"host": 7, "port": 1}, "host"),
        ({"host": "db", "port": 1, "debug": "yes"}, "debug"),
        ({"host": "db", "port": 1, "tags": ["a", 2]}, "tags"),
        ({"host": "db", "port": 1, "tags": "a"}, "tags"),
    ]
    for data, field in cases:
        with pytest.raises(ConfigError, match=field):
            ServerConfig.from_dict(data)


def test_missing_required_field_is_named():
    with pytest.raises(ConfigError, match="host"):
        ServerConfig.from_dict({"port": 80})


def test_unknown_key_is_named():
    with pytest.raises(ConfigError, match="colour"):
        ServerConfig.from_dict({"host": "a", "port": 1, "colour": "red"})
