import json

from config import load_config, merge


def write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return path


def test_nested_sections_merge_at_every_depth(tmp_path):
    d = write(tmp_path, "d.json", {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4})
    u = write(tmp_path, "u.json", {"a": {"b": {"d": 20}}})
    assert load_config(d, u, {"a": {"b": {"x": 9}}}) == {"a": {"b": {"c": 1, "d": 20, "x": 9}, "e": 3}, "f": 4}


def test_lists_and_scalars_replace(tmp_path):
    d = write(tmp_path, "d.json", {"k": {"items": [1, 2], "n": 1}})
    assert load_config(d, None, {"k": {"items": [3]}}) == {"k": {"items": [3], "n": 1}}


def test_missing_user_file_is_ignored(tmp_path):
    d = write(tmp_path, "d.json", {"a": {"b": 1}})
    assert load_config(d, tmp_path / "nope.json") == {"a": {"b": 1}}


def test_merge_does_not_change_its_inputs():
    base = {"a": {"b": {"c": 1}}}
    other = {"a": {"b": {"c": 2}}}
    merge(base, other)
    assert base == {"a": {"b": {"c": 1}}}
    assert other == {"a": {"b": {"c": 2}}}
