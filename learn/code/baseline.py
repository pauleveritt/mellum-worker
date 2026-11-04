"""Provenance and compact reporting for the trusted Vanilla collection."""

import fcntl
import base64
import hashlib
import json
import os
import re
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


def worker_hashes(repo: Path) -> dict:
    """Freeze the worker and its local import closure, including type imports."""
    pending = [repo / "extensions/mellum-worker.ts"]
    hashes = {}
    while pending:
        path = pending.pop().resolve()
        name = str(path.relative_to(repo.resolve()))
        if name in hashes:
            continue
        hashes[name] = sha256(path)
        pending.extend(path.parent / rel for rel in re.findall(r'from\s+[\"\'](\.[^\"\']+)[\"\']', path.read_text()))
    return hashes


def create_manifest(repo: Path, preflight: dict, *, arm: str = "vanilla") -> dict:
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
                "arm":arm, "extensions":["extensions/mellum-recorder.ts"],
                "context_files":False, "cold_context":True}
    if arm == "worker":
        material.update(extensions=["extensions/mellum-worker.ts", "extensions/mellum-recorder.ts"],
                        arm_env={"MELLUM_MODE":"1"}, worker_hashes=worker_hashes(repo))
    return {"schema":1, "created_at":datetime.now(UTC).isoformat(),
            "command":"uv run python learn/code/harness.py baseline",
            "source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
            "material":material, "attempts":[]}


def attach_reference(current: dict, path: Path) -> None:
    """Fail closed on shared-input drift; preserve the reviewed instrument delta."""
    saved = json.loads(path.read_text())
    reference = saved["material"]
    if (saved.get("status") != "complete" or reference.get("arm") != "vanilla"
            or counted_attempts(saved["attempts"]) != 6
            or any(a["state"] == "pending-review" for a in saved["attempts"])):
        raise SystemExit("reference must be a complete six-counted Vanilla batch")
    if current["material"].get("isolation"):
        ignored = {"arm", "extensions", "arm_env", "worker_hashes"}
        shared = {k:v for k,v in current["material"].items() if k not in ignored}
        expected = {k:v for k,v in reference.items() if k not in ignored}
        if shared != expected or reference.get("extensions") != ["extensions/mellum-recorder.ts"]:
            raise SystemExit("shared contained reference inputs mismatch; a fresh contained Vanilla reference is required")
        current["reference"] = {"path":str(path.resolve()), "sha256":sha256(path)}
        return
    shared = {k:v for k,v in current["material"].items()
              if k not in {"arm", "extensions", "arm_env", "worker_hashes"}}
    expected = {k:v for k,v in reference.items() if k not in {"arm", "extensions"}}
    if reference.get("extensions") != ["extensions/mellum-recorder.ts"]:
        raise SystemExit("reference must have recorder-only extensions")
    instruments = {"learn/code/harness.py", "learn/code/baseline.py"}
    delta = {name:{"reference":expected["hashes"][name], "current":shared["hashes"][name]}
             for name in instruments}
    shared["hashes"] = {k:v for k,v in shared["hashes"].items() if k not in instruments}
    expected["hashes"] = {k:v for k,v in expected["hashes"].items() if k not in instruments}
    if shared != expected:
        differing = sorted(k for k in set(shared) | set(expected) if shared.get(k) != expected.get(k))
        raise SystemExit(f"shared reference inputs mismatch: {differing}")
    proof_path = path.parent / "native-max-tokens-verification.json"
    observations_path = path.parent / "runtime-observations.json"
    proof = json.loads(proof_path.read_text())
    observations = json.loads(observations_path.read_text())
    runtime = observations["pi_runtime"]
    pi = current["material"]["pi"]
    if runtime["entryPath"] != pi["entry_path"] or runtime["piVersion"] != pi["version"]:
        raise SystemExit("reference Pi runtime identity mismatch")
    package = Path(pi["entry_path"]).parents[2]
    hashes = {str(package / name):digest for name,digest in proof["runtime_sha256"].items()}
    if not hashes or any(not Path(p).is_file() or sha256(Path(p)) != digest for p,digest in hashes.items()):
        raise SystemExit("reference runtime hashes changed")
    node = runtime["execPath"]
    version = subprocess.check_output([node, "--version"], text=True).strip()
    if observations.get("node_version", version) != version:
        raise SystemExit("reference Node runtime version changed")
    hashes[node] = sha256(Path(node))
    current["material"]["runtime"] = {"exec_path":node, "node_version":version, "hashes":hashes}
    current["reference"] = {"path":str(path.resolve()), "sha256":sha256(path),
        "supplement_sha256":sha256(proof_path), "observations_sha256":sha256(observations_path),
        "instrument_delta":delta,
        "scope":"Bundle hashes are post-Vanilla supplements; Node binary hash is pinned prospectively."}
    current["command"] += f" --arm worker --reference {path}"


def verify_collection_inputs(repo: Path, material: dict) -> None:
    if material.get("isolation"):
        from containment import image_info
        if image_info(material["isolation"]["image"]) != material["isolation"]:
            raise SystemExit("contained runtime/policy inputs changed")
    hashes = {**material["hashes"], **material.get("worker_hashes", {})}
    if any(sha256(repo / name) != digest for name,digest in hashes.items()):
        raise SystemExit("collection source inputs changed")
    if any(sha256(Path(name)) != digest for name,digest in material.get("runtime", {}).get("hashes", {}).items()):
        raise SystemExit("collection runtime inputs changed")


def validate_resume(saved: dict, current: dict) -> None:
    if saved["material"] != current["material"] or saved.get("reference") != current.get("reference"):
        raise SystemExit("material collection inputs changed; refusing to resume")


def classify_attempt(record: dict, *, identity_ok: bool) -> tuple[str, str]:
    if record.get("instrumentation_error"):
        return "pending-review", "instrumentation diagnostic sink failed"
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


def reconcile_attempts(batch: Path, attempts: list[dict], pi: dict, *, arm: str = "vanilla", exec_path: str | None = None,
                       isolation: dict | None = None) -> None:
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
                       identity_ok=verify_trace_identity(run, pi, arm=arm, exec_path=exec_path,
                           isolation=isolation), cleanup_ok=record.get("cleanup_ok"),
                       reason="completed run record recovered after interruption; explicit classification required")


def worker_activation(run: Path) -> bool:
    """Native Pi persists a second model_change when headless activate calls setModel.

    With the pinned runtime and exact worker/recorder launch, this read-only
    evidence distinguishes successful startup from a worker that stayed off.
    """
    sessions = list((run / "sessions").glob("*.jsonl"))
    if len(sessions) != 1:
        return False
    rows = [json.loads(line) for line in sessions[0].read_text().splitlines() if line.strip()]
    before_user = []
    for row in rows:
        if row.get("type") == "message" and row.get("message", {}).get("role") == "user":
            break
        if row.get("type") == "model_change":
            before_user.append((row.get("provider"), row.get("modelId")))
    return before_user == [("llamacpp", "Mellum2.1-12B-A2.5B-Thinking")] * 2


def verify_trace_identity(run: Path, pi: dict, *, arm: str = "vanilla", exec_path: str | None = None,
                          isolation: dict | None = None) -> bool:
    try:
        launch = json.loads((run / "launch.json").read_text())
        argv = launch["argv"]
        extensions = [argv[i+1] for i, arg in enumerate(argv) if arg == "-e"]
        rows = [json.loads(line) for line in (run / "trace.jsonl").read_text().splitlines() if line.strip()]
        starts = [row for row in rows if row.get("type") == "instance_start"]
        internal = Path("/attempt/runs") / run.name if isolation else run
        if isolation:
            boundary = json.loads((run / "containment.json").read_text())
            if boundary.get("image") != isolation["image"] or not boundary.get("container_removed"):
                return False
        expected = [str(internal / "record-pi.mjs")]
        if arm == "worker":
            expected.insert(0, "/opt/instrument/extensions/mellum-worker.ts" if isolation else str(REPO / "extensions/mellum-worker.ts"))
            if (launch.get("arm_env") != {"MELLUM_MODE":"1"}
                    or launch.get("mode_runs_file") != str(internal / "mellum-mode-runs.jsonl")
                    or not worker_activation(run)):
                return False
        return (launch["arm"] == arm and not launch["extras"] and not launch["context_files"]
                and extensions == expected
                and all(flag in argv for flag in ("--no-context-files","--no-skills","--no-extensions"))
                and bool(starts) and all(row.get("runId") == run.name
                    and row.get("runtime", {}).get("piVersion") == pi["version"]
                    and row.get("runtime", {}).get("entryPath") == pi["entry_path"]
                    and (exec_path is None or row.get("runtime", {}).get("execPath") == exec_path) for row in starts))
    except (OSError, ValueError, KeyError, IndexError):
        return False


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def require_containment(image: str | None, qualification: Path | None) -> dict:
    if not image or not qualification:
        raise SystemExit("trusted collection requires --isolation-image and --isolation-qualification; native containment is unverified")
    from containment import image_info
    material = image_info(image)
    proof = json.loads(qualification.read_text())
    if proof.get("qualified") is not True or proof.get("material") != material:
        raise SystemExit("containment qualification is missing, failed or mismatched")
    return material


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
    paths = [*root.glob("*/owner.json"), *root.glob("*-easy-*/attempt-*/*/owner.json")]
    for path in sorted(paths):
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
