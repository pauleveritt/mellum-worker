"""Boundary regressions; real Docker qualification is a separate explicit command."""
import io
import json
import sys
import subprocess
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import containment


def archive(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as tar:
        for name, kind in entries:
            item = tarfile.TarInfo(name)
            item.type = kind
            item.linkname = "/etc/passwd" if kind == tarfile.SYMTYPE else ""
            item.size = 1 if kind == tarfile.REGTYPE else 0
            tar.addfile(item, io.BytesIO(b"x") if item.size else None)
    stream.seek(0)
    return stream


@pytest.mark.parametrize("entries", [
    [("../escape", tarfile.REGTYPE)], [("/escape", tarfile.REGTYPE)],
    [("workspace/link", tarfile.SYMTYPE)], [("workspace/link", tarfile.LNKTYPE)],
    [("workspace/fifo", tarfile.FIFOTYPE)],
    [("workspace/x", tarfile.REGTYPE), ("workspace/x", tarfile.REGTYPE)],
    [("workspace/x", tarfile.REGTYPE), ("workspace/x/y", tarfile.REGTYPE)],
])
def test_export_rejects_escaping_links_duplicates_and_collisions(tmp_path, entries):
    with pytest.raises(ValueError):
        containment.extract_regular(archive(entries), tmp_path / "staging")
    assert not (tmp_path / "escape").exists()


def test_export_limits_and_runtime_exclusion(tmp_path):
    containment.extract_regular(archive([("workspace/a", tarfile.REGTYPE),
        ("workspace/.venv/python", tarfile.SYMTYPE)]), tmp_path / "good")
    assert (tmp_path / "good/workspace/a").read_bytes() == b"x"
    assert not (tmp_path / "good/workspace/.venv").exists()
    with pytest.raises(ValueError, match="limit"):
        containment.extract_regular(archive([("a", tarfile.REGTYPE)]), tmp_path / "large", max_bytes=0)


def test_policy_has_no_host_access_and_uses_immutable_image():
    argv = containment.create_argv("sha256:" + "a" * 64, "owner-test")
    for pair in [("--network", "none"), ("--cap-drop", "ALL"),
                 ("--security-opt", "no-new-privileges"), ("--user", "1000:1000")]:
        index = argv.index(pair[0])
        assert argv[index + 1] == pair[1]
    assert "--read-only" in argv
    assert not any(a in argv for a in ["--privileged", "-v", "--volume", "--pid", "--env-file"])
    assert argv[argv.index("--mount") + 1] == "type=volume,source=mellum-attempt-owner-test,target=/attempt"
    assert not any("/attempt:" in a for a in argv)
    with pytest.raises(ValueError, match="image"):
        containment.create_argv("latest", "test")


def test_environment_is_an_allowlist(monkeypatch):
    monkeypatch.setenv("CONTAINMENT_SENTINEL_SECRET", "private")
    env = containment.agent_environment()
    assert "CONTAINMENT_SENTINEL_SECRET" not in env
    assert not any(k in env for k in ["SSH_AUTH_SOCK", "OPENAI_API_KEY", "NODE_OPTIONS"])


def test_private_volume_is_bounded_and_owned():
    argv = containment.volume_argv("test")
    assert "type=tmpfs" in argv and "device=tmpfs" in argv
    assert "o=size=1g,uid=1000,gid=1000,mode=0700" in argv
    assert "mellum.measurement.owner=test" in argv
    assert argv[-1] == "mellum-attempt-test"


def test_contained_remedies_map_only_trusted_repository_units():
    unit = containment.REPO / "remedies/guard/foreground-server.ts"
    assert containment.contained_extras([unit]) == ["/opt/instrument/remedies/guard/foreground-server.ts"]
    for path in (containment.REPO / "learn/code/harness.py", Path("/tmp/arbitrary.ts")):
        with pytest.raises(ValueError, match="remedy"):
            containment.contained_extras([path])


def test_model_input_never_contains_oracle_names_or_canary():
    import harness
    suite = harness.load_suite(harness.SUITES, "easy")
    public = containment.suite_data(suite)
    assert "expected" not in public and "canary" not in public


@pytest.mark.parametrize("code", ["import time; time.sleep(300)",
    "import os, signal; os.kill(os.getpid(), signal.SIGSTOP)"])
def test_host_watchdog_bounds_stalled_or_stopped_commands(code):
    with pytest.raises(subprocess.TimeoutExpired):
        containment.run_bounded_command([sys.executable, "-c", code], timeout=.1)


def test_exported_control_filenames_are_never_recovery_authority(tmp_path, monkeypatch):
    import baseline
    artifact = tmp_path / "vanilla-easy-batch/attempt-01/run/workspace"
    artifact.mkdir(parents=True)
    for name in ("owner.json", "container.json"):
        (artifact / name).write_text("{}")
    def forbidden(*args, **kwargs):
        pytest.fail("model artifact reached host cleanup authority")
    monkeypatch.setattr(containment, "remove_owned", forbidden)
    monkeypatch.setattr(baseline, "process_identity", forbidden)
    containment.recover(tmp_path)
    assert baseline.reap_stale_runs(tmp_path) == []


def test_trusted_collection_requires_qualified_containment_before_preflight(monkeypatch):
    import harness
    monkeypatch.setattr(harness, "BASELINE_RUNS", Path("/must-not-create"))
    with pytest.raises(SystemExit, match="containment|isolation"):
        harness.collect_baseline()
