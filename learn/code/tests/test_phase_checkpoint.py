"""F.8: only a trusted accepted phase becomes a checkpoint, and the next phase starts only from a verified one."""
import json
import shutil

import pytest

import harness
import phase_boundary
from test_harness import FIX, PROFILE
from test_phase_boundary_run import GOOD, SUITES, phase_run, phased


def accepted_checkpoint(tmp_path, monkeypatch):
    run_dir, record = phase_run(tmp_path / "one", monkeypatch)
    assert record["boundary"]["accepted"] is True, record["boundary"]["reasons"]
    return run_dir / "checkpoint", record


def phase_two(tmp_path, monkeypatch, checkpoint):
    monkeypatch.delenv("FAKE_APP", raising=False)
    return harness._run_sessions(phased(2), runs_dir=tmp_path / "two", pi_binary=str(FIX / "fake-pi-phase.mjs"),
                                 repeat=1, grade_run=True, deadline=None, profile=PROFILE, phase=2,
                                 from_checkpoint=checkpoint)


def test_an_accepted_phase_is_checkpointed_with_its_manifest(tmp_path, monkeypatch):
    (tmp_path / "one").mkdir()
    checkpoint, record = accepted_checkpoint(tmp_path, monkeypatch)
    manifest = json.loads((checkpoint / "checkpoint.json").read_text())
    assert manifest["suite"] == "phased" and manifest["phase"] == 1
    assert manifest["grader"] == record["grader"] and manifest["boundary"]["accepted"] is True
    assert record["checkpoint"]["commit"] == manifest["commit"] and len(manifest["commit"]) == 40
    assert (checkpoint / "tree" / "app.py").read_text() == GOOD
    assert (checkpoint / "tree" / ".git").is_dir()


def test_a_rejected_phase_makes_no_checkpoint(tmp_path, monkeypatch):
    run_dir, record = phase_run(tmp_path, monkeypatch, app="ONE = 2\n")
    assert record["boundary"]["accepted"] is False
    assert not (run_dir / "checkpoint").exists() and record["checkpoint"] is None


def test_the_next_phase_starts_from_the_checkpoint_without_its_git(tmp_path, monkeypatch):
    (tmp_path / "one").mkdir()
    checkpoint, _ = accepted_checkpoint(tmp_path, monkeypatch)
    [result] = phase_two(tmp_path, monkeypatch, checkpoint)
    workspace = result[0] / "workspace"
    assert (workspace / "app.py").read_text() == GOOD
    assert not (workspace / ".git").exists()
    record = json.loads((result[0] / "run.json").read_text())
    assert record["from_checkpoint"]["phase"] == 1
    assert record["boundary"]["accepted"] is False  # this fake never adds TWO


def test_a_changed_checkpoint_is_refused_before_any_session(tmp_path, monkeypatch):
    (tmp_path / "one").mkdir()
    checkpoint, _ = accepted_checkpoint(tmp_path, monkeypatch)
    (checkpoint / "tree" / "app.py").write_text(GOOD + "TWO = 2\n")
    with pytest.raises(SystemExit, match="changed"):
        phase_two(tmp_path, monkeypatch, checkpoint)
    assert not (tmp_path / "two").exists()


def test_a_checkpoint_of_another_phase_or_suite_is_refused(tmp_path, monkeypatch):
    (tmp_path / "one").mkdir()
    checkpoint, _ = accepted_checkpoint(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="phase 1"):
        phase_boundary.verify_checkpoint(checkpoint, phased(3), 3)
    manifest = json.loads((checkpoint / "checkpoint.json").read_text())
    (checkpoint / "checkpoint.json").write_text(json.dumps({**manifest, "suite": "easy"}))
    with pytest.raises(SystemExit, match="easy"):
        phase_boundary.verify_checkpoint(checkpoint, phased(2), 2)


def test_the_earlier_phase_is_graded_again_and_a_regression_refused(tmp_path, monkeypatch):
    """A checkpoint whose files and manifest agree can still fail today's acceptance (a changed grader)."""
    (tmp_path / "one").mkdir()
    checkpoint, _ = accepted_checkpoint(tmp_path, monkeypatch)
    (checkpoint / "tree" / "app.py").write_text("ONE = 2\nONE_LABEL = \"one\"\n")
    manifest = json.loads((checkpoint / "checkpoint.json").read_text())
    manifest["files"] = phase_boundary.tree_hashes(checkpoint / "tree")
    (checkpoint / "checkpoint.json").write_text(json.dumps(manifest))
    with pytest.raises(SystemExit, match="no longer accepted"):
        phase_boundary.verify_checkpoint(checkpoint, phased(2), 2)


def test_no_venv_or_cache_reaches_a_checkpoint_and_its_digest_is_stable(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    (build / "app.py").write_text(GOOD)
    for junk in (".venv/lib/x.py", "__pycache__/app.cpython-314.pyc", ".pytest_cache/v"):
        (build / junk).parent.mkdir(parents=True, exist_ok=True)
        (build / junk).write_text("junk")
    out = tmp_path / "checkpoint"
    verdict = phase_boundary.accept_saved(build, phased(1))
    phase_boundary.write_checkpoint(build, phased(1), verdict, out)
    tree = out / "tree"
    assert not any((tree / name).exists() for name in (".venv", "__pycache__", ".pytest_cache"))
    first = phase_boundary.verify_checkpoint(out, phased(2), 2)
    second = phase_boundary.verify_checkpoint(out, phased(2), 2)
    assert first["files"] == second["files"]


def test_the_checkpoint_command_records_contamination_not_checked_without_a_trace(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    (build / "app.py").write_text(GOOD)
    out = tmp_path / "checkpoint"
    code = harness.main(["checkpoint", "--workspace", str(build), "--suite", "phased", "--suites-dir", str(SUITES),
                         "--phase", "1", "--out", str(out)])
    assert code == 0
    manifest = json.loads((out / "checkpoint.json").read_text())
    assert manifest["boundary"]["contaminated"] == "not_checked" and manifest["boundary"]["accepted"] is True


def test_the_checkpoint_command_refuses_a_failing_build(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    (build / "app.py").write_text("ONE = 2\n")
    out = tmp_path / "checkpoint"
    assert harness.main(["checkpoint", "--workspace", str(build), "--suite", "phased", "--suites-dir", str(SUITES),
                         "--phase", "1", "--out", str(out)]) == 1
    assert not out.exists()


def test_the_cli_needs_a_checkpoint_after_phase_one(capsys):
    with pytest.raises(SystemExit):
        harness.main(["run", "--suite", "easy", "--phase", "2", "--dry-run"])
    assert "--from-checkpoint" in capsys.readouterr().err
