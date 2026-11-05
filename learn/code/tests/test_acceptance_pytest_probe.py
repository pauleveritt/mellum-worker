"""A writable JUnit file and exit(0) cannot attest that tests executed."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[3] / "scripts/containment/pytest_probe.py"


@pytest.mark.parametrize("code,conftest,valid", [
    ("def test_ok(): assert True\n", "", True),
    ("", "", False),
    ("import pytest\n@pytest.mark.skip\ndef test_skip(): pass\n", "", False),
    ("def test_wrong(): assert False\n", "", False),
    ("def test_never(): assert False\n", 'from pathlib import Path\nimport os\nPath("/tmp/probe-tests.xml").write_text(\'<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>\')\nos._exit(0)\n', False),
])
def test_fixed_pytest_launcher_requires_executed_reports_and_normal_finish(tmp_path, code, conftest, valid):
    tests = tmp_path / "tests"; tests.mkdir()
    (tests / "test_candidate.py").write_text(code)
    (tests / "conftest.py").write_text(conftest)
    result = subprocess.run([sys.executable, "-I", str(RUNNER)], cwd=tmp_path,
                            capture_output=True, timeout=10)
    try:
        data = json.loads(result.stdout)
    except ValueError:
        data = {}
    accepted = bool(result.returncode == 0 and data.get("completed") is True
                    and data.get("passed", 0) > 0 and data.get("failures") == 0
                    and data.get("errors") == 0)
    assert accepted is valid, (result.returncode, result.stdout, result.stderr)
