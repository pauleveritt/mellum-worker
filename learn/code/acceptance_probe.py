"""Candidate execution boundary. Only bounded data crosses back to trusted assertions."""
import json
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from containment import Container


class CandidateProbe:
    def __init__(self, image: str, snapshot: Path, control: Path, *, deadline_at: float):
        self.image, self.snapshot, self.control, self.deadline_at = image, snapshot, control, deadline_at
        self.container = Container(image, control / (".grading-" + uuid.uuid4().hex))

    def __enter__(self):
        self.container.__enter__()
        try:
            with tempfile.TemporaryDirectory(prefix="mellum-probe-") as temporary:
                seed = Path(temporary)
                shutil.copytree(self.snapshot, seed / "workspace")
                self.container.seed(seed)
            return self
        except BaseException:
            self.container.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        self.container.__exit__(*args)

    def run(self, name: str, inputs: dict, timeout: float) -> dict:
        if name not in {"home", "titles", "startup", "tests"}:
            raise ValueError("unsupported fixed candidate probe")
        remaining = min(timeout, self.deadline_at - time.monotonic())
        if remaining <= 0:
            raise subprocess.TimeoutExpired(name, timeout)
        command = 'cd /attempt/workspace && exec /opt/dependencies/.venv/bin/python -I /opt/probe.py "$1"'
        with tempfile.TemporaryFile() as output:
            try:
                result = subprocess.run(self.container.exec_argv("sh", "-c", command, "probe", name, interactive=True),
                    input=json.dumps(inputs).encode(), stdout=output, stderr=subprocess.STDOUT, timeout=remaining)
            except subprocess.TimeoutExpired:
                return {"probe_error": "candidate probe timed out"}
            output.seek(0)
            raw = output.read(1024 * 1024 + 1)
        if result.returncode or len(raw) > 1024 * 1024:
            return {"probe_error": "candidate probe exited or exceeded output bound", "exit_code": result.returncode}
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {"probe_error": "invalid observation"}
        except (ValueError, UnicodeDecodeError):
            return {"probe_error": "candidate produced no valid observation"}
