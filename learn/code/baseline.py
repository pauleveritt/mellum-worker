"""Provenance and compact reporting for the trusted Vanilla collection."""

import fcntl
import base64
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FREEZE = REPO / "docs/superpowers/research/2026-11-03-runpod-qualification/config.json"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def resolve_pinned_pi(repo: Path, *, candidates=None) -> dict:
    pin = dict(line.split("=", 1) for line in (repo / "scripts/pi-pin.env").read_text().splitlines()
               if line and not line.startswith("#"))
    candidates = candidates if candidates is not None else [Path.home()/".local/bin/pi", shutil.which("pi")]
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        try:
            result = subprocess.run([str(candidate), "--version"], capture_output=True,
                                    text=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and result.stdout.strip() == pin["PI_VERSION"]:
            return {"path": str(Path(candidate).absolute()), "entry_path": str(Path(candidate).resolve()),
                    "version": pin["PI_VERSION"]}
    raise SystemExit(f"Pi {pin['PI_VERSION']} required; install: npm install -g {pin['PI_PACKAGE']}@{pin['PI_VERSION']}")


def read_json_url(base: str, route: str):
    try:
        with urllib.request.urlopen(base + route, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError) as error:
        raise SystemExit(f"backend preflight {route} failed: {error}") from error


def expected_server_argv(config: dict) -> list[str]:
    s = config["server"]
    host, port = s["bind"].rsplit(":", 1)
    return ["/workspace/mellum/llama.cpp/build/bin/llama-server", "-m",
        "/workspace/mellum/cache/"+config["model"]["file"], "-a", config["model"]["alias"],
        "--host", host, "--port", port, "-c", str(s["requested_total_context"]),
        "-np", str(s["parallel_slots"]), "--no-kv-unified", "--jinja", "-fa", s["flash_attention"],
        "--cont-batching", "-t", str(s["threads"]), "-tb", str(s["batch_threads"]),
        "-b", str(s["batch"]), "-ub", str(s["microbatch"]),
        "-ctk", s["cache_type_k"], "-ctv", s["cache_type_v"], "-ngl", str(s["gpu_layers"])]


def verify_remote(config: dict) -> dict:
    """Read live hardware, running executable, weights and argv over pinned SSH."""
    connection = config["connection"]
    command = ["ssh", "-i", str(Path(connection["key_path"]).expanduser()),
        "-p", str(connection["port"]), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=20", "-o", "StrictHostKeyChecking=yes", "-o",
        "UserKnownHostsFile="+str(REPO / connection["known_hosts"]),
        connection["user"]+"@"+connection["host"], "bash -s"]
    # Fixed paths deliberately avoid interpolating remote shell text from configuration.
    script = r'''set -euo pipefail
server_pid=$(pgrep -f '^/workspace/mellum/llama.cpp/build/bin/llama-server ')
test "$(printf '%s\n' "$server_pid" | wc -l)" -eq 1
printf 'gpu|'
nvidia-smi --query-gpu=name,memory.total,driver_version,uuid --format=csv,noheader,nounits
printf 'weight|'
sha256sum /workspace/mellum/cache/Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf
printf 'executable|'
sha256sum /proc/$server_pid/exe
for binary in /workspace/mellum/llama.cpp/build/bin/*; do
  printf 'binary|'
  sha256sum "$binary"
done
printf 'argv|'
base64 -w0 /proc/$server_pid/cmdline
printf '\n'
'''
    try:
        result = subprocess.run(command, input=script, capture_output=True, text=True,
                                timeout=600, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f"backend SSH provenance failed: {error}") from error
    if result.returncode:
        raise SystemExit(f"backend SSH provenance failed: {result.stderr}")
    live = {"runtime_sha256": {}}
    for line in result.stdout.splitlines():
        kind, _, value = line.partition("|")
        if kind == "gpu":
            gpu, memory, driver, uuid = [part.strip() for part in value.split(",")]
            live.update(gpu=gpu, vram_mib=int(memory), driver=driver, gpu_uuid=uuid)
        elif kind == "weight":
            live["weight_sha256"] = value.split()[0]
        elif kind == "executable":
            live["executable_sha256"] = value.split()[0]
        elif kind == "binary":
            digest, path = value.split()
            live["runtime_sha256"][Path(path).name] = digest
        elif kind == "argv":
            live["cmdline"] = base64.b64decode(value).decode().rstrip("\0").split("\0")
    if live.get("executable_sha256") != config["backend"]["runtime_sha256"]["llama-server"]:
        raise SystemExit("running backend executable identity mismatch")
    return live


def checker_versions() -> dict[str, str]:
    versions = {}
    import re
    import tomllib
    suite_project = tomllib.loads((REPO / "learn/code/suites/easy/base/pyproject.toml").read_text())
    pytest_requirement = next(req for req in suite_project["dependency-groups"]["dev"] if req.startswith("pytest=="))
    for name in ("ruff", "complexipy", "pyrefly", "pytest"):
        requirement = pytest_requirement if name == "pytest" else name
        result = subprocess.run(["uvx", "--from", requirement, name, "--version"], capture_output=True,
                                text=True, check=False, timeout=120)
        match = re.search(r"\b\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?", result.stdout)
        if result.returncode or match is None:
            raise SystemExit(f"cannot freeze checker {name}: {result.stdout} {result.stderr}")
        versions[name] = match.group()
    return versions


def preflight(pi_binary: Path, profile: Path) -> dict:
    config = json.loads(FREEZE.read_text())
    if config["status"] != "frozen_infrastructure_screen_passed":
        raise SystemExit("backend configuration is not qualified")
    pi = resolve_pinned_pi(REPO, candidates=[pi_binary])
    effective = json.loads((profile / "models.json").read_text())
    if sha256(profile / "models.json") != config["client"]["profile_sha256"]:
        raise SystemExit("model profile identity mismatch")
    provider = effective["providers"]["llamacpp"]
    provider["baseUrl"] = config["client"]["collection_base_url"]
    base = provider["baseUrl"].removesuffix("/v1")
    health = read_json_url(base, "/health")
    props = read_json_url(base, "/props")
    models = read_json_url(base, "/v1/models")
    slots = read_json_url(base, "/slots")
    expected_build = f"b{config['backend']['build_number']}-{config['backend']['source_revision'][:9]}"
    if health != {"status": "ok"}:
        raise SystemExit("backend health is not ready")
    if props.get("build_info") != expected_build or props.get("model_alias") != config["model"]["alias"]:
        raise SystemExit("backend build/model identity mismatch")
    if props.get("model_ftype") != "Q4_K - Medium" or props.get("model_path") != "/workspace/mellum/cache/"+config["model"]["file"]:
        raise SystemExit("backend model quantization/path identity mismatch")
    if not any(model.get("id") == config["model"]["alias"] and model.get("owned_by") == "llamacpp"
               for model in models.get("data", [])):
        raise SystemExit("backend model identity mismatch")
    if len(slots) != config["server"]["parallel_slots"] or any(
        slot.get("n_ctx") != config["server"]["effective_context_per_slot"] or slot.get("is_processing") is not False
        for slot in slots):
        raise SystemExit("backend context/slots mismatch or another request is active")
    live = verify_remote(config)
    expected = {"gpu": config["hardware"]["gpu"], "vram_mib": config["hardware"]["vram_mib"],
                "driver": config["hardware"]["driver"], "weight_sha256": config["model"]["sha256"],
                "runtime_sha256": config["backend"]["runtime_sha256"], "cmdline": expected_server_argv(config)}
    if any(live.get(key) != value for key, value in expected.items()):
        raise SystemExit("backend live provenance/config identity mismatch")
    stable_props = {key:props[key] for key in ("build_info","model_alias","model_ftype","model_path","total_slots")}
    return {"pi": pi, "effective_profile": effective, "checkers": checker_versions(),
            "backend": {"freeze": config, "live": live, "props": stable_props},
            "profile_settings": json.loads((profile / "settings.json").read_text())}


def create_manifest(repo: Path, preflight: dict) -> dict:
    from harness import file_hashes, machine_label
    hashes = {}
    for name in ("learn/code/harness.py", "learn/code/baseline.py", "extensions/mellum-recorder.ts",
                 "scripts/pi-pin.env", "scripts/backend.py", "pyproject.toml", "uv.lock"):
        hashes[name] = sha256(repo / name)
    for rel, digest in file_hashes(repo / "learn/code/suites/easy").items():
        hashes["learn/code/suites/easy/"+rel] = digest
    # Freeze file contents, not a mutable model name or an unrelated binary on PATH.
    material = {**preflight, "hashes": hashes, "machine": machine_label(),
                "pi_entry_sha256": sha256(Path(preflight["pi"]["entry_path"])),
                "limits": {"deadline":600,"stall":180,"target":6,"concurrency":1},
                "arm":"vanilla", "extensions":["extensions/mellum-recorder.ts"],
                "context_files":False, "cold_context":True}
    return {"schema":1, "created_at":datetime.now(UTC).isoformat(),
            "command":"uv run python learn/code/harness.py baseline",
            "source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
            "material":material, "attempts":[]}


def validate_resume(saved: dict, current: dict) -> None:
    if saved["material"] != current["material"]:
        raise SystemExit("material collection inputs changed; refusing to resume")


def classify_attempt(record: dict, *, identity_ok: bool) -> tuple[str, str]:
    if not identity_ok:
        return "pending-review", "missing or mismatched runtime/launch identity"
    if not record.get("cleanup_ok"):
        return "pending-review", "cleanup failed"
    if record.get("grading_infrastructure_error"):
        return "pending-review", "grading infrastructure failed to start"
    if record.get("provider_error"):
        return "pending-review", "provider error: " + record["provider_error"]["classification"]
    if not record.get("requests"):
        return "pending-review", "no provider request observed"
    return "counted", "model execution (including failure, stall or deadline)"


def counted_attempts(attempts: list[dict]) -> int:
    return sum(attempt["state"] == "counted" for attempt in attempts)


def resolve_attempt(attempts: list[dict], run_id: str, state: str, reason: str) -> None:
    if not reason.strip():
        raise SystemExit("an explicit evidence-based reason is required")
    attempt = next((a for a in attempts if a["run_id"] == run_id), None)
    if attempt is None or attempt["state"] != "pending-review":
        raise SystemExit("only a pending-review attempt may be classified; counted attempts are immutable")
    if state == "counted" and (not attempt.get("path") or not attempt.get("identity_ok")
                               or not attempt.get("cleanup_ok")):
        raise SystemExit("incomplete attempt has no verified record/identity/cleanup; cannot count it")
    attempt["state"] = state
    attempt["reason"] = reason


def verify_private_profile(batch: Path, material: dict) -> None:
    for name, expected in (("models.json", material["effective_profile"]),
                           ("settings.json", material["profile_settings"])):
        try:
            actual = json.loads((batch / "profile" / name).read_text())
        except (OSError, ValueError) as error:
            raise SystemExit(f"private profile unreadable: {error}") from error
        if actual != expected:
            raise SystemExit(f"private profile changed: {name}")
    if {p.name for p in (batch / "profile").iterdir()} != {"models.json", "settings.json"}:
        raise SystemExit("unexpected private profile inputs; refusing changed configuration")


def reconcile_attempts(batch: Path, attempts: list[dict], pi: dict) -> None:
    """Recover durable results left between record persistence and ledger commit."""
    for attempt in attempts:
        if attempt["state"] != "pending-review" or attempt.get("path"):
            continue
        records = list((batch / attempt["directory"]).glob("*/run.json"))
        if len(records) > 1:
            raise SystemExit("ambiguous retained attempt records; refusing replacement")
        if not records:
            continue
        run = records[0].parent
        record = json.loads(records[0].read_text())
        attempt.update(run_id=run.name, path=str(run.relative_to(batch)),
                       identity_ok=verify_trace_identity(run, pi), cleanup_ok=record.get("cleanup_ok"),
                       reason="completed run record recovered after interruption; explicit classification required")


def verify_trace_identity(run: Path, pi: dict) -> bool:
    try:
        launch = json.loads((run / "launch.json").read_text())
        argv = launch["argv"]
        extensions = [argv[i+1] for i, arg in enumerate(argv) if arg == "-e"]
        rows = [json.loads(line) for line in (run / "trace.jsonl").read_text().splitlines() if line.strip()]
        starts = [row for row in rows if row.get("type") == "instance_start"]
        return (launch["arm"] == "vanilla" and not launch["extras"] and not launch["context_files"]
                and extensions == [str(run / "record-pi.mjs")]
                and all(flag in argv for flag in ("--no-context-files","--no-skills","--no-extensions"))
                and bool(starts) and all(row.get("runId") == run.name
                    and row.get("runtime", {}).get("piVersion") == pi["version"]
                    and row.get("runtime", {}).get("entryPath") == pi["entry_path"] for row in starts))
    except (OSError, ValueError, KeyError, IndexError):
        return False


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
