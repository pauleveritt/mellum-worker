import csv

from cleaner import dedupe


def run(tmp_path, text):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    src.write_text(text)
    dedupe(src, out)
    with open(out, newline="") as handle:
        return list(csv.DictReader(handle)), out.read_text().splitlines()[0]


def test_one_row_per_id_in_first_seen_order(tmp_path):
    rows, header = run(tmp_path, "id,v,updated_at\n7,a,2026-01-01T00:00:00\n3,b,2026-01-02T00:00:00\n"
                                 "7,c,2026-01-03T00:00:00\n")
    assert header == "id,v,updated_at"
    assert [r["id"] for r in rows] == ["7", "3"]


def test_keeps_the_newest_even_when_it_comes_first(tmp_path):
    rows, _ = run(tmp_path, "id,v,updated_at\n1,new,2026-05-01T12:00:00\n2,x,2026-01-01T00:00:00\n"
                            "1,old,2026-04-30T23:59:59\n")
    assert {r["id"]: r["v"] for r in rows} == {"1": "new", "2": "x"}


def test_other_columns_are_preserved(tmp_path):
    rows, header = run(tmp_path, "name,id,updated_at,note\nz,9,2026-02-02T00:00:00,keep\n")
    assert header == "name,id,updated_at,note"
    assert rows == [{"name": "z", "id": "9", "updated_at": "2026-02-02T00:00:00", "note": "keep"}]
