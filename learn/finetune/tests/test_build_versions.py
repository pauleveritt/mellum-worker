"""build_dpo_phases never overwrites an existing training set: each build is a new, versioned folder."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def test_refuses_an_existing_output_folder(tmp_path):
    out = tmp_path / "data_dpo_x"
    out.mkdir()
    (out / "train.jsonl").write_text("keep me\n")
    done = subprocess.run([sys.executable, str(HERE / "build_dpo_phases.py"), "--model", "unused", "--out", str(out)],
                          capture_output=True, text=True)
    assert done.returncode != 0 and "already exists" in done.stderr
    assert (out / "train.jsonl").read_text() == "keep me\n"
