"""Fixed observer: emit reports only after pytest returns normally.

Candidate tests still execute untrusted code; this is behavioral observation,
not an authenticity guarantee against deliberate interpreter monkeypatching.
"""
import contextlib
import io
import json
import sys
from pathlib import Path

import pytest


class Reports:
    def __init__(self):
        self.passed = self.failures = self.errors = self.skipped = 0
        self.finished = False

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped += 1
        elif report.when == "call":
            self.passed += report.passed
            self.failures += report.failed
        elif report.failed:
            self.errors += 1

    def pytest_sessionfinish(self, session, exitstatus):
        self.finished = True


if __name__ == "__main__":
    reports = Reports()
    # Import the fixed observer/pytest before putting candidate imports on path.
    sys.path.insert(0, str(Path.cwd()))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        status = pytest.main(["tests", "-q"], plugins=[reports])
    print(json.dumps({"completed": reports.finished, "exit_code": int(status),
        "tests": reports.passed + reports.failures + reports.skipped,
        "passed": reports.passed, "failures": reports.failures,
        "errors": reports.errors, "skipped": reports.skipped}))
    raise SystemExit(status)
