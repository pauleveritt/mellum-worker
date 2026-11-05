"""The acceptance package's candidate probe, run natively (LC.39).

Same trusted checker and package hash as the contained gate; only the boundary
moves. Candidate code runs as the grading user on a private copy of the snapshot,
never on the session's own tree, and the user is swept afterwards.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from acceptance import AcceptancePackage
from baseline import write_json
from harness import sweep_workspace
from isolation import RIG_USERS, sweep_user

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/containment"
OPERATIONS = {"home", "titles", "startup", "tests"}
MAX_OUTPUT = 1024 * 1024


class NativeProbe:
    def __init__(self, snapshot: Path, control: Path, *, deadline_at: float, user: str | None, python: Path,
                 env: dict | None = None):
        self.snapshot, self.control, self.deadline_at = Path(snapshot), Path(control), deadline_at
        self.user, self.python, self.base_env = user, Path(python), env
        self.root = None

    def __enter__(self):
        self.control.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="mellum-native-probe-"))
        shutil.copytree(self.snapshot, self.root / "workspace", symlinks=True)
        (self.root / "tmp").mkdir()
        for name in ("probe.py", "pytest_probe.py"):
            shutil.copy2(SCRIPTS / name, self.root / name)
        if self.user is not None:
            for path in [self.root, *self.root.rglob("*")]:
                shutil.chown(path, user=self.user)
        return self

    def __exit__(self, *args):
        workspace = self.root / "workspace"
        sweep_workspace(workspace)
        if self.user in RIG_USERS:
            sweep_user(self.user)
        shutil.rmtree(self.root, ignore_errors=True)

    def run(self, name: str, inputs: dict, timeout: float) -> dict:
        if name not in OPERATIONS:
            raise ValueError("unsupported fixed candidate probe")
        remaining = min(timeout, self.deadline_at - time.monotonic())
        if remaining <= 0:
            raise subprocess.TimeoutExpired(name, timeout)
        env = {**(self.base_env if self.base_env is not None else os.environ),
               "MELLUM_PYTEST_PROBE": str(self.root / "pytest_probe.py"),
               "MELLUM_PROBE_TMP": str(self.root / "tmp")}
        env.pop("VIRTUAL_ENV", None)
        argv = [str(self.python), "-I", str(self.root / "probe.py"), name]
        with tempfile.TemporaryFile() as output:
            child = subprocess.Popen(argv, cwd=self.root / "workspace", env=env, stdin=subprocess.PIPE,
                                     stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
                                     **({"user": self.user} if self.user is not None else {}))
            try:
                child.communicate(json.dumps(inputs).encode(), timeout=remaining)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(child.pid, 9)
                except ProcessLookupError:
                    pass
                child.wait()
                return {"probe_error": "candidate probe timed out"}
            finally:
                sweep_workspace(self.root / "workspace")
            output.seek(0)
            raw = output.read(MAX_OUTPUT + 1)
        if child.returncode or len(raw) > MAX_OUTPUT:
            return {"probe_error": "candidate probe exited or exceeded output bound", "exit_code": child.returncode}
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {"probe_error": "invalid observation"}
        except (ValueError, UnicodeDecodeError):
            return {"probe_error": "candidate produced no valid observation"}


def check_snapshot_native(snapshot: Path, package: AcceptancePackage, control: Path, timeout: float, *,
                          user: str | None, python: Path, env: dict | None = None) -> dict:
    """Run the package's frozen checker against a snapshot, with candidate code in NativeProbe."""
    control = Path(control)
    control.mkdir(parents=True, exist_ok=True)
    if not package.verify():
        result = {"status": "integrity_error"}
    else:
        timeout = min(timeout, package.timeout)
        until = time.monotonic() + timeout
        if timeout <= 0:
            result = {"status": "timeout"}
        else:
            try:
                namespace = {"__file__": str(package.root / package.checker), "__name__": "acceptance_checker"}
                exec(compile((package.root / package.checker).read_bytes(), namespace["__file__"], "exec"), namespace)
                with NativeProbe(snapshot, control, deadline_at=until, user=user, python=python, env=env) as probe:
                    result = namespace["evaluate"](Path(snapshot), probe, lambda: max(0, until - time.monotonic()))
                if time.monotonic() > until:
                    result = {"status": "timeout"}
            except subprocess.TimeoutExpired:
                result = {"status": "timeout"}
            except Exception as error:
                result = {"status": "checker_error", "detail": f"{type(error).__name__}: {error}"[:2000]}
        if not package.verify():
            result = {"status": "integrity_error"}
    if user is None:
        result = {**result, "uncontained": True}
    write_json(control / "checker-result.json", result)
    return result
