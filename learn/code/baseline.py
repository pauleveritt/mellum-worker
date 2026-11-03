"""Provenance and compact reporting for the trusted Vanilla collection."""

import fcntl
import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def process_identity(pid: int) -> dict | None:
    result = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                            capture_output=True, text=True, check=False)
    if result.returncode == 1 and not result.stdout.strip():
        return None
    if result.returncode != 0 or not result.stdout.strip():
        raise SystemExit(f"cannot verify process identity for pid {pid}: {result.stderr}")
    return {"pid": pid, "start": result.stdout.strip()}


@contextmanager
def collection_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".baseline.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("another collection is active (runs root locked)") from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def reap_stale_runs(root: Path) -> list[dict]:
    from harness import group_members, sweep_group, sweep_workspace, workspace_members
    recovered = []
    for path in sorted(root.glob("**/owner.json")):
        run = path.parent
        execution_path = run / "execution.json"
        if execution_path.is_file() and json.loads(execution_path.read_text()).get("cleanup_ok"):
            continue
        if (run / "recovery.json").is_file():
            if json.loads((run / "recovery.json").read_text()).get("cleanup_ok"):
                continue
        owner = json.loads(path.read_text())
        workspace = run / "workspace"
        if run.is_symlink() or workspace.is_symlink() or str(workspace.resolve()) != owner.get("workspace"):
            raise SystemExit(f"unverifiable workspace ownership: {run}")
        identity = owner["owner"]
        if process_identity(identity["pid"]) == identity:
            raise SystemExit(f"run has an active owner: {run}")
        children = owner["children"]
        # Validate all identities before any signal: a recycled PID is never authority.
        live = []
        for child in children:
            current = process_identity(child["pid"])
            if current is not None and current != child:
                raise SystemExit(f"child identity mismatch; refusing ambiguous ownership: {run}")
            if current is not None:
                live.append(child)
        killed = []
        for child in live:
            killed.extend(sweep_group(child["pid"]))
        killed.extend(sweep_workspace(workspace))
        ok = not workspace_members(workspace) and not any(group_members(c["pid"]) for c in live)
        record = {"run_id": run.name, "cleanup_ok": ok, "reaped": killed,
                  "reason": "owner exited without verified cleanup"}
        write_json(run / "recovery.json", record)
        recovered.append(record)
        if not ok:
            raise SystemExit(f"stale run cleanup failed: {run}")
    return recovered


def render_scorecard(records: list[dict]) -> str:
    lines = ["| Run | Hidden checks | Code health | Completion | Model turns | Output tokens | Elapsed seconds |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for record in records:
        checks = f"{record.get('checks_passed', 0)}/{record.get('checks_total', 0)}"
        if not record.get("checks_ran"):
            checks = f"not run ({checks})"
        values = [record.get("run_id", "unknown"), checks,
                  record.get("code_health", "not checked"), record.get("completion", "error"),
                  record.get("turns"), record.get("output_tokens"), record.get("elapsed_seconds")]
        lines.append("| " + " | ".join("unknown" if value is None else str(value).replace("|", "\\|")
                                      for value in values) + " |")
    return "\n".join(lines) + "\n"
