"""pairs_io: pair sets are written in sections, every file under GitHub's size limit, and read back in order."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pairs_io import MAX_BYTES, read_pairs, section, write_pairs  # noqa: E402

REPO = Path(__file__).resolve().parents[3]


def rows():
    kinds = ["medium:p2", "medium:p3:step", "medium:p2:outside", "medium:p4", "medium:p2:unused", "medium:p3:step"]
    return [{"phase": k, "chosen": list(range(10 * (i + 1))), "n": i} for i, k in enumerate(kinds * 5)]


def test_section_names_the_pair_kind():
    assert [section(r) for r in rows()[:6]] == ["phase", "step", "outside", "phase", "unused", "step"]
    assert section({"phase": "py3.15-x:p1:idiom"}) == "idiom"


def test_write_splits_by_section_and_size_and_reads_back_in_order(tmp_path):
    original = rows()
    write_pairs(tmp_path, "train", original, max_bytes=2000)
    files = sorted(p.name for p in tmp_path.iterdir())
    assert {f.split(".")[1] for f in files} == {"phase", "step", "outside", "unused"}
    assert len([f for f in files if ".phase." in f]) > 1  # a big section is cut into numbered parts
    assert all((tmp_path / f).stat().st_size <= 2000 for f in files)
    assert read_pairs(tmp_path, "train") == original  # exact rows, exact order


def test_one_row_bigger_than_the_limit_is_refused(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        write_pairs(tmp_path, "train", [{"phase": "medium:p2", "chosen": list(range(5000))}], max_bytes=1000)


def test_read_accepts_an_older_single_file_set(tmp_path):
    (tmp_path / "valid.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows()))
    assert read_pairs(tmp_path, "valid") == rows()


def test_no_committed_file_is_over_the_limit():
    tracked = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True,
                             check=True).stdout.split("\0")
    big = [(f, (REPO / f).stat().st_size) for f in tracked
           if f and (REPO / f).is_file() and (REPO / f).stat().st_size > MAX_BYTES]
    assert big == [], f"files over {MAX_BYTES} bytes: {big}"
