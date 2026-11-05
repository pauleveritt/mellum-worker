"""The acceptance package's probe, run natively (LC.39): same checker, same hash, no container."""
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import acceptance_native
from acceptance import AcceptancePackage
from acceptance_qualification import PACKAGE, fixture

PINNED = "af4122164322e6446b5cb12728693ca32749fdaec2606aa35e1bcaf9e41e3dd9"
DEPENDENCIES = Path(__file__).resolve().parents[1] / "suites/easy/base"


@pytest.fixture(scope="module")
def probe_python(tmp_path_factory) -> Path:
    """The frozen dependency project's interpreter, as the bootstrap syncs it on a pod."""
    project = tmp_path_factory.mktemp("deps")
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copy2(DEPENDENCIES / name, project / name)
    subprocess.run(["uv", "sync", "--offline", "--frozen", "--project", str(project), "--python", "3.14"],
                   check=True, capture_output=True, timeout=300)
    return project / ".venv/bin/python"


def test_package_hash_unchanged():
    assert AcceptancePackage.load(PACKAGE).digest == PINNED


def test_native_known_good_passes(tmp_path, probe_python):
    fixture(tmp_path / "good")
    result = acceptance_native.check_snapshot_native(tmp_path / "good", AcceptancePackage.load(PACKAGE),
                                                     tmp_path / "control", 90, user=None, python=probe_python)
    assert result["status"] == "pass", result
    assert (tmp_path / "control/checker-result.json").is_file()


def test_native_known_broken_fails(tmp_path, probe_python):
    fixture(tmp_path / "broken")
    (tmp_path / "broken/app.py").write_text("syntax broken!!\n")
    result = acceptance_native.check_snapshot_native(tmp_path / "broken", AcceptancePackage.load(PACKAGE),
                                                     tmp_path / "control", 90, user=None, python=probe_python)
    assert result["status"] == "fail"
    assert result["checks"]["guarded_reload"]["passed"] is False


def test_native_probe_rejects_unknown_name(tmp_path, probe_python):
    fixture(tmp_path / "good")
    with acceptance_native.NativeProbe(tmp_path / "good", tmp_path / "control", deadline_at=time.monotonic() + 30,
                                       user=None, python=probe_python) as probe:
        with pytest.raises(ValueError, match="unsupported"):
            probe.run("shell", {}, 5)


def test_native_probe_times_out_on_a_hung_startup(tmp_path, probe_python):
    fixture(tmp_path / "hung")
    (tmp_path / "hung/app.py").write_text("import time\ntime.sleep(60)\n")
    started = time.monotonic()
    with acceptance_native.NativeProbe(tmp_path / "hung", tmp_path / "control", deadline_at=time.monotonic() + 30,
                                       user=None, python=probe_python) as probe:
        result = probe.run("startup", {}, 3)
    assert time.monotonic() - started < 20
    assert result.get("probe_error") or result.get("ready") is False


def test_native_probe_works_on_a_copy(tmp_path, probe_python):
    fixture(tmp_path / "good")
    before = sorted(p.relative_to(tmp_path / "good") for p in (tmp_path / "good").rglob("*"))
    with acceptance_native.NativeProbe(tmp_path / "good", tmp_path / "control", deadline_at=time.monotonic() + 60,
                                       user=None, python=probe_python) as probe:
        probe.run("tests", {}, 30)
    assert sorted(p.relative_to(tmp_path / "good") for p in (tmp_path / "good").rglob("*")) == before
