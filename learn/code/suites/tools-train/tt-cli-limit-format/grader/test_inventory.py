import json

from inventory import main


def make_csv(tmp_path):
    path = tmp_path / "stock.csv"
    path.write_text("name,qty\nmango,3\napple,90\nkiwi,15\nbanana,90\n")
    return str(path)


def test_existing_sort_flag_still_works(tmp_path, capsys):
    main([make_csv(tmp_path), "--sort", "qty"])
    names = [line.split()[0] for line in capsys.readouterr().out.splitlines()]
    assert names == ["apple", "banana", "kiwi", "mango"]


def test_limit_applies_after_sorting(tmp_path, capsys):
    main([make_csv(tmp_path), "--sort", "name", "--limit", "2"])
    names = [line.split()[0] for line in capsys.readouterr().out.splitlines()]
    assert names == ["apple", "banana"]


def test_json_format_with_int_quantities(tmp_path, capsys):
    main([make_csv(tmp_path), "--format", "json", "--sort", "qty", "--limit", "3"])
    assert json.loads(capsys.readouterr().out) == [
        {"name": "apple", "qty": 90}, {"name": "banana", "qty": 90}, {"name": "kiwi", "qty": 15}]
