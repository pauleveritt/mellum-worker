"""Trusted host adapter. Docker mailbox content can request checks, never certify them."""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from acceptance import AcceptancePackage, Gate
from baseline import write_json


def parse_request(raw: str, *, task_id: str, sequence: int) -> dict:
    if len(raw) > 16000:
        raise ValueError("acceptance request limit")
    try:
        item = json.loads(raw)
        if (not isinstance(item, dict) or set(item) != {"task_id", "request_id", "sequence"}
                or item["task_id"] != task_id or type(item["sequence"]) is not int
                or item["sequence"] != sequence
                or not isinstance(item["request_id"], str)
                or not re.fullmatch(r"[a-f0-9]{32}", item["request_id"])):
            raise ValueError("invalid acceptance request")
        return item
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("invalid acceptance request") from error


def snapshot_digest(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("snapshot link")
        if path.is_file():
            rows.append((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def evaluate_snapshot(snapshot: Path, package: AcceptancePackage, image: str,
                      control: Path, timeout: float) -> dict:
    # Only the operator's frozen, hash-verified code is executed on the host.
    # Candidate Python is executed only by CandidateProbe in its own container.
    from acceptance_probe import CandidateProbe
    if not package.verify():
        return {"status": "integrity_error"}
    until = time.monotonic() + min(timeout, package.timeout)
    if timeout <= 0:
        return {"status": "timeout"}
    try:
        namespace = {"__file__": str(package.root / package.checker), "__name__": "acceptance_checker"}
        exec(compile((package.root / package.checker).read_bytes(), namespace["__file__"], "exec"), namespace)
        with CandidateProbe(image, snapshot, control, deadline_at=until) as probe:
            result = namespace["evaluate"](snapshot, probe, lambda: max(0, until - time.monotonic()))
        if time.monotonic() > until:
            result = {"status": "timeout"}
    except subprocess.TimeoutExpired:
        result = {"status": "timeout"}
    except Exception as error:
        result = {"status": "checker_error", "detail": f"{type(error).__name__}: {error}"[:2000]}
    if not package.verify():
        result = {"status": "integrity_error"}
    return result


def check_snapshot(snapshot: Path, package: AcceptancePackage, image: str,
                   control: Path, timeout: float) -> dict:
    from containment import recover
    control.mkdir(parents=True, exist_ok=True)
    if not package.verify():
        return {"status": "integrity_error"}
    timeout = min(timeout, package.timeout)
    if timeout <= 0:
        return {"status": "timeout"}
    argv = [sys.executable, str(Path(__file__).resolve()), "--evaluate", str(snapshot.resolve()),
            str(package.root), image, str(control.resolve()), str(timeout)]
    with (control / "checker-output.txt").open("w") as output:
        try:
            process = subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
            path = control / "checker-result.json"
            if process.returncode or not path.is_file() or path.stat().st_size > 1024 * 1024:
                result = {"status": "checker_error", "detail": "checker process exited without a bounded result"}
            else:
                result = json.loads(path.read_text())
        except subprocess.TimeoutExpired:
            result = {"status": "timeout"}
        finally:
            # A killed trusted checker may have left its labelled probe container.
            recover(control)
    if not package.verify():
        result = {"status": "integrity_error"}
    write_json(control / "checker-result.json", result)
    return result


READ_MAILBOX = """
const fs=require('fs'),p='/attempt/gate/request.json';
try {const s=fs.lstatSync(p);if(!s.isFile()||s.size>16000)process.exit(2);
process.stdout.write(fs.readFileSync(p));}catch(e){if(e.code!=='ENOENT')process.exit(2);}
"""
WRITE_REPLY = """
const fs=require('fs'),s=fs.readFileSync(0,'utf8');
fs.writeFileSync('/attempt/gate/reply.tmp',s);fs.renameSync('/attempt/gate/reply.tmp','/attempt/gate/reply.json');
"""


def run_model_with_gate(container, argv: list[str], gate: Gate, workspace: str,
                        control: Path, output) -> subprocess.CompletedProcess:
    seen = set()
    previous_raw = ""
    child = subprocess.Popen(argv, stdout=output, stderr=subprocess.STDOUT)
    try:
        while child.poll() is None:
            if gate.remaining() <= 0:
                raise subprocess.TimeoutExpired(argv, 600)
            read = subprocess.run(container.exec_argv("node", "-e", READ_MAILBOX),
                                  capture_output=True, text=True, timeout=min(3, gate.remaining()))
            raw = read.stdout
            if read.returncode:
                raise ValueError("invalid acceptance mailbox")
            if raw and raw != previous_raw:
                request = parse_request(raw, task_id=gate.task_id, sequence=gate.checks + 1)
                if request["request_id"] in seen or gate.checks >= gate.max_repairs + 1:
                    raise ValueError("duplicate or excessive acceptance request")
                seen.add(request["request_id"])
                previous_raw = raw
                check_control = control / f"check-{gate.checks + 1}"
                container.snapshot(workspace, check_control / "snapshot")
                snapshot = check_control / "snapshot/workspace"
                result = check_snapshot(snapshot, gate.package, container.image, check_control,
                                        min(gate.package.timeout, gate.remaining()))
                receipt = gate.apply(result, snapshot_digest(snapshot))
                write_json(control / "gate-journal.json", gate.journal)
                reply = {**{k: receipt[k] for k in ("task_id", "status", "continue", "feedback")},
                         "request_id": request["request_id"], "sequence": request["sequence"]}
                subprocess.run(container.exec_argv("node", "-e", WRITE_REPLY, interactive=True),
                    input=json.dumps(reply), text=True, check=True, timeout=min(3, max(.01, gate.remaining())))
            time.sleep(.15)
        return subprocess.CompletedProcess(argv, child.returncode)
    except ValueError:
        gate.status = "integrity_error"
        raise
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        write_json(control / "gate-journal.json", gate.journal)


if __name__ == "__main__" and sys.argv[1] == "--evaluate":
    snapshot, package, image, control, timeout = sys.argv[2:]
    result = evaluate_snapshot(Path(snapshot), AcceptancePackage.load(Path(package)), image, Path(control), float(timeout))
    write_json(Path(control) / "checker-result.json", result)
