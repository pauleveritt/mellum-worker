#!/usr/bin/env python3
"""Run one eval suite through base Pi in a fresh directory and score it.

The ladder measures; this teaches. A suite is a project with a mission,
tech stack and roadmap; its hidden graders stay out of the workspace until
the child has exited, and the run lives outside the repo.
"""

from __future__ import annotations

import argparse
import fnmatch
import platform
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

CODE = Path(__file__).resolve().parent
RUNS = Path(tempfile.gettempdir()) / "mellum-eval-runs"
SUITES = CODE / "suites"
RECORDER = CODE.parent.parent / "extensions" / "mellum-recorder.ts"
PROFILE = CODE / "profile"
EXTENSION = CODE.parents[1] / "extensions" / "mellum-worker.ts"
# The think-tag repair (a no-op on a correctly served reply). The flow loads it in every session; in
# the harness it is the remedy unit context/repair-think-tags, listed by the lines that want it.
THINK_TAGS = CODE.parents[1] / "extensions" / "mellum-think-tags.ts"
BUDGET_PROXY = CODE / "budget-proxy.mjs"
REMEDIES = CODE.parents[1] / "remedies"
ARMS = ("vanilla", "bare", "worker", "strip-thinking")
# Every knob an arm may set. A run clears them from the inherited environment
# first, so an exported value cannot make two arms the same policy. The decoupled
# worker reads only these two; the old guards/prompt/facts env vars are gone with
# the ablation arms that set them — ablation is a `--remedy` now, not an `--arm`.
ARM_ENV_KEYS = ("MELLUM_MODE", "MELLUM_STRIP_THINKING")
FLAGS = [
    "-p", "--no-approve", "--no-extensions", "--no-skills",
    "--no-prompt-templates", "--no-themes", "--no-context-files",
]


@dataclass(frozen=True)
class Suite:
    name: str
    prompts: list[str]
    tests: Path
    start: Path | None
    expected: tuple[str, ...] = ()
    canary: str | None = None
    root: Path | None = None
    layout: dict | None = None
    # Caps on run.json fields (record.json): a failure that lives in the record.
    record: dict | None = None
    grader_revision: str = "current"
    grader_base: Path | None = None
    # The session budget (budget.json): requests and output tokens, enforced at a proxy (F.5).
    budget: dict | None = None

    @property
    def prompt(self) -> str:
        return self.prompts[0]


def _read_prompt(path: Path) -> str:
    text = path.read_text().strip()
    if not text:
        raise SystemExit(f"empty prompt: {path}")
    return text


def load_suite(suites_dir: Path, name: str) -> Suite:
    base = Path(suites_dir) / name
    prompts_dir = base / "prompts"
    if prompts_dir.is_dir():
        files = sorted(prompts_dir.glob("*.md"))
        if not files:
            raise SystemExit(f"no prompts in {prompts_dir}")
        prompts = [_read_prompt(path) for path in files]
    else:
        prompts = [_read_prompt(base / "task.md")]
    grader = base / "grader"
    expected = ()
    if (base / "expected.json").is_file():
        expected = tuple(json.loads((base / "expected.json").read_text()))
    canary = None
    if (grader / "canary").is_file():
        canary = (grader / "canary").read_text().strip() or None
    start = base / "start"
    layout = None
    if (base / "layout.json").is_file():
        layout = json.loads((base / "layout.json").read_text())
    record = None
    if (base / "record.json").is_file():
        record = json.loads((base / "record.json").read_text())
    budget = json.loads((base / "budget.json").read_text()) if (base / "budget.json").is_file() else None
    return Suite(
        name=name,
        prompts=prompts,
        tests=grader if grader.is_dir() else base / "tests",
        start=start if start.is_dir() else None,
        expected=expected,
        canary=canary,
        root=base,
        layout=layout,
        record=record,
        budget=budget,
    )


def record_failures(metrics: dict, caps: dict | None) -> list[str]:
    """The run.json fields over a challenge's caps, as reasons a learner can read."""
    return [f"{key} is {metrics.get(key, 0)} (at most {cap})"
            for key, cap in (caps or {}).items() if (metrics.get(key) or 0) > cap]


def profile_pin(profile_dir: Path) -> tuple[str, str]:
    providers = json.loads((Path(profile_dir) / "models.json").read_text())["providers"]
    provider = next(iter(providers))
    return provider, providers[provider]["models"][0]["id"]


def new_run(runs_dir: Path, name: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run = Path(runs_dir) / f"{stamp}-{name}-{uuid.uuid4().hex[:6]}"
    run.mkdir(parents=True)
    return run


def arm_settings(arm: str) -> dict:
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}; choose from {', '.join(ARMS)}")
    if arm == "vanilla":
        # The true floor: no worker extension at all, only the recorder (added by pi_argv). Every
        # guard and remedy must then come in explicitly through --remedy. This is the base the
        # lessons build up from, with nothing hidden.
        return {"extension": None, "env": {}}
    if arm == "bare":
        # The worker is always loaded, even on the bare arm, but mode stays off (no MELLUM_MODE), so
        # bare still sends vanilla Pi's requests — MELLUM_MODE=1 below is what engages the worker.
        # The baseline tests pin that worker-off is inert.
        return {"extension": EXTENSION, "env": {}}
    # Only worker and strip-thinking reach here (vanilla and bare returned above).
    env = {"MELLUM_MODE": "1"}
    if arm == "strip-thinking":
        # Opens the seam the worker closes by default (A12): earlier reasoning is
        # dropped from the payload, everything else identical. The worker reads
        # MELLUM_STRIP_THINKING directly; it is the one ablation arm still live
        # after the decoupling. The rest ablated bundle parts the worker no longer
        # has, so they are gone — ablate with a `--remedy` unit instead.
        env["MELLUM_STRIP_THINKING"] = "1"
    return {"extension": EXTENSION, "env": env}


# Windows has no ps, lsof, killpg or SIGKILL: processes are listed through CIM,
# a run's "group" is the tree under the Pi child (orphans keep their parent's
# pid), and a kill is taskkill /T /F, which ends the whole tree at once.
WINDOWS = os.name == "nt"
KILL_SIGNALS = (signal.SIGTERM,) if WINDOWS else (signal.SIGTERM, signal.SIGKILL)
# A Windows child's job object, by its pid. A process stays in its job after its
# parent exits, so the job finds a server the model backgrounded from a shell
# that is gone, which a parent-pid walk cannot.
JOBS: dict[int, int] = {}

if WINDOWS:
    import ctypes
    from ctypes import wintypes

    _K32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _K32.CreateJobObjectW.restype = wintypes.HANDLE
    _K32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    _K32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _K32.QueryInformationJobObject.argtypes = (
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p)
    _K32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _NTDLL = ctypes.WinDLL("ntdll")
    _NTDLL.NtResumeProcess.argtypes = (wintypes.HANDLE,)

    class _JobPids(ctypes.Structure):
        _fields_ = [("assigned", wintypes.DWORD), ("listed", wintypes.DWORD),
                    ("ids", ctypes.c_size_t * 4096)]

    class _JobLimits(ctypes.Structure):  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION
        _fields_ = [("per_process_time", ctypes.c_int64), ("per_job_time", ctypes.c_int64),
                    ("flags", wintypes.DWORD), ("min_ws", ctypes.c_size_t),
                    ("max_ws", ctypes.c_size_t), ("active_limit", wintypes.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                    ("scheduling", wintypes.DWORD), ("io", ctypes.c_uint64 * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

    _K32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)


# The suite app's documented port. A server left on it answers for the model's own app, so a
# session does not start while anything listens there (LC.41: a stray one answered for 13 hours).
GUARDED_PORTS = (8000,)


def guarded_listeners(ports) -> list[dict]:
    """Loopback listeners on ports, each named by pid and command where lsof can say."""
    import socket
    found = []
    for port in ports:
        with socket.socket() as probe:
            probe.settimeout(1)
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                continue
        row = {"port": port, "pid": None, "command": None}
        if shutil.which("lsof"):
            out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-F", "pc"],
                                 capture_output=True, text=True, timeout=30).stdout
            for line in out.splitlines():
                if line[:1] == "p" and row["pid"] is None:
                    row["pid"] = int(line[1:])
                elif line[:1] == "c" and row["command"] is None:
                    row["command"] = line[1:]
        found.append(row)
    return found


PROJECT_MARKERS = ("pyproject.toml", ".git")


def project_above(path: Path) -> Path | None:
    """The marker of a project that holds path, if any: what uv and pip discover upward from a
    workspace. Runs inside one let a session install into that project's venv (LC.41)."""
    for folder in [Path(path).resolve(), *Path(path).resolve().parents]:
        for marker in PROJECT_MARKERS:
            if (folder / marker).exists():
                return folder / marker
    return None


def pi_version(pi_binary: str) -> str | None:
    """The version the Pi binary reports, or None when it cannot say. Run outside any workspace."""
    try:
        out = subprocess.run([pi_binary, "--version"], capture_output=True, text=True, timeout=10,
                             cwd=tempfile.gettempdir(), stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"\d+\.\d+\.\d+", out.stdout + out.stderr) if out.returncode == 0 else None
    return match.group() if match else None


def proxy_target(base_url: str) -> tuple[str, str]:
    """Split a provider baseUrl into the root the budget proxy forwards to and the path Pi keeps."""
    from urllib.parse import urlsplit
    parts = urlsplit(base_url)
    return f"{parts.scheme}://{parts.netloc}/", parts.path.rstrip("/")


def is_loopback(target: str) -> bool:
    from urllib.parse import urlsplit
    return urlsplit(target).hostname == "127.0.0.1"


def start_budget_proxy(budget: dict, target: str, log: Path) -> tuple[subprocess.Popen, int]:
    """Start the session's budget proxy and wait for its ready row; returns it and its port.

    It runs in a group of its own (start_child), because `node` may be a shim (Volta) whose
    child is the real proxy; stop_budget_proxy ends the whole group. Its stderr is kept beside
    the log, and a proxy that does not start says why."""
    stderr = Path(log).with_name("proxy-stderr.txt")
    with stderr.open("w") as errors:
        proxy = start_child(["node", str(BUDGET_PROXY), "--target", target, "--log", str(log),
                             "--max-requests", str(budget["max_requests"]),
                             "--max-output", str(budget["max_output_tokens"]),
                             "--unknown-charge", str(budget["unknown_usage_charge"]), "--listen", "0"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=errors)
    try:
        until = time.monotonic() + 10
        while time.monotonic() < until and proxy.poll() is None:
            for row in _jsonl(log):
                if row.get("boundary") == "ready":
                    return proxy, row["port"]
            time.sleep(0.05)
    except BaseException:
        stop_budget_proxy(proxy)
        raise
    stop_budget_proxy(proxy)
    reason = stderr.read_text().strip().splitlines()[-1:] if stderr.is_file() else []
    raise SystemExit(f"the budget proxy did not start ({reason[0] if reason else 'no error printed'}); "
                     "no session was started")


def stop_budget_proxy(proxy: subprocess.Popen) -> None:
    kill_tree(proxy.pid)
    try:
        proxy.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proxy.kill()
        proxy.wait()


def _jsonl(path: Path) -> list[dict]:
    rows = []
    if Path(path).is_file():
        for line in Path(path).read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass      # a row still being written
    return rows


def budget_exhausted(budget_log: Path | None) -> bool:
    return budget_log is not None and any(row.get("boundary") == "budget_exhausted" for row in _jsonl(budget_log))


def budget_record(run: Path) -> dict | None:
    """The limits a run was given and what it spent, from its proxy log; None for an unbudgeted run."""
    limits = Path(run) / "budget-limits.json"
    if not limits.is_file():
        return None
    rows = _jsonl(Path(run) / "proxy.jsonl")
    return {"limits": json.loads(limits.read_text()),
            "spent": {"requests": sum(r.get("boundary") == "created" and r.get("method") == "POST" for r in rows),
                      "output_tokens": sum(r.get("charged") or 0 for r in rows if r.get("boundary") == "usage")}}


def host_gate(card_path: Path, endpoint: str, pins: dict) -> dict:
    """Refuse a counted run unless its host card passed, for this pin card and the server live now (F.5).

    The live server must match what was checked: build, model, slots, and every server flag
    except the ones that may vary between restarts (conformance.VARIABLE_FLAGS)."""
    import conformance
    card = json.loads(Path(card_path).read_text())
    problems = []
    if card.get("schema") != conformance.SCHEMA or card.get("passed") is not True:
        problems.append("the host card did not pass")
    if card.get("pins_digest") != conformance.pins_digest(pins):
        problems.append("the host card was made for another pin card")
    try:
        props = conformance._get(endpoint, "/props")
        slots = [slot.get("n_ctx") for slot in conformance._get(endpoint, "/slots")]
    except OSError as error:
        raise SystemExit(f"the model server at {endpoint} did not answer ({error}); no session was started")
    for key, live in (("build_info", props.get("build_info")), ("model_path", props.get("model_path")),
                      ("slots", slots)):
        if card.get(key) != live:
            problems.append(f"{key} is {live!r} now, {card.get(key)!r} on the card")
    command = conformance.server_command(int(endpoint.rsplit(":", 1)[1].split("/")[0]))
    if command is None or conformance.pinned_flags(command) != conformance.pinned_flags(card.get("server_command") or []):
        problems.append("the server was restarted with other flags since the card was made")
    if problems:
        raise SystemExit("not a counted run: " + "; ".join(problems) +
                         ". Rerun conformance.py for this server, or run without --host-card (uncounted).")
    return {"path": str(card_path), "sha256": conformance.sha256_file(card_path), "passed": True}


def session_path(path: str, virtual_env: str | None) -> str:
    """PATH for a session without the harness's own venv: `uv run` puts it first, and a session
    that inherits it runs the repository's python and uvicorn instead of the workspace's."""
    venvs = {Path(v) / "bin" for v in (virtual_env, sys.prefix if sys.prefix != sys.base_prefix else None) if v}
    return os.pathsep.join(entry for entry in path.split(os.pathsep) if entry and Path(entry) not in venvs)


def start_child(argv: list[str], **kwargs) -> subprocess.Popen:
    """Start a child in a group of its own: a session on POSIX, a job object on Windows.

    On Windows the child starts suspended and resumes only once it is in its
    job, so nothing it starts can escape the job.
    """
    argv = native_argv(argv)
    if not WINDOWS:
        return subprocess.Popen(argv, start_new_session=True, **kwargs)
    child = subprocess.Popen(argv, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                             | 0x00000004, **kwargs)  # CREATE_SUSPENDED
    handle = int(child._handle)  # type: ignore[attr-defined]
    job = _K32.CreateJobObjectW(None, None)
    if job:
        # Stopping a run on Windows is a hard kill, so no sweep runs: have the OS end
        # the job's processes when the harness, which holds the job's handle, dies.
        limits = _JobLimits(flags=0x2000)  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        _K32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits))
    if job and _K32.AssignProcessToJobObject(job, handle):
        JOBS[child.pid] = job
    _NTDLL.NtResumeProcess(handle)
    return child


def job_pids(job: int) -> list[int]:
    """The live processes in a Windows job object."""
    pids = _JobPids()
    if not _K32.QueryInformationJobObject(job, 3, ctypes.byref(pids), ctypes.sizeof(pids), None):
        return []  # 3: JobObjectBasicProcessIdList
    return [int(pids.ids[i]) for i in range(pids.listed)]


def native_argv(argv: list[str]) -> list[str]:
    """On Windows, run an npm .cmd shim's script with node directly, and a .sh through bash.

    Pi installs as pi.cmd, and cmd.exe would mangle a multi-line prompt that
    holds < > % or quotes. Elsewhere the argv is returned unchanged.
    """
    if not WINDOWS:
        return argv
    if argv[0].lower().endswith(".sh") and Path(argv[0]).is_file():
        # Windows cannot start a shell script itself; run it through bash (Git Bash).
        return [shutil.which("bash") or "bash", *argv]
    found = shutil.which(argv[0])
    if found is None:
        return argv
    if found.lower().endswith((".cmd", ".bat")):
        shim = Path(found).read_text(errors="ignore")
        script = re.search(r'"%dp0%\\([^"]+\.[cm]?js)"', shim)
        if script:
            base = Path(found).parent
            node = base / "node.exe"
            launcher = str(node) if node.is_file() else (shutil.which("node") or "node")
            return [launcher, str(base / script.group(1)), *argv[1:]]
    return [found, *argv[1:]]


def windows_processes() -> list[dict]:
    """Every live process on Windows: ProcessId, ParentProcessId, ExecutablePath, CommandLine."""
    query = ("Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,"
             "ExecutablePath,CommandLine | ConvertTo-Json -Compress")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", query],
                             capture_output=True, text=True, check=False, timeout=60).stdout
        rows = json.loads(out or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    return rows if isinstance(rows, list) else [rows]


def _command(row: dict) -> str:
    return (row.get("CommandLine") or row.get("ExecutablePath") or "").strip()


def windows_tree(root: int) -> list[tuple[int, str]]:
    """The live processes under `root` (and root itself), by parent pid."""
    rows = windows_processes()
    children: dict[int, list[dict]] = {}
    for row in rows:
        children.setdefault(row["ParentProcessId"], []).append(row)
    found = [(row["ProcessId"], _command(row)) for row in rows if row["ProcessId"] == root]
    stack, seen = [root], {root, os.getpid()}
    while stack:
        for row in children.get(stack.pop(), []):
            pid = row["ProcessId"]
            if pid not in seen:
                seen.add(pid)
                found.append((pid, _command(row)))
                stack.append(pid)
    return [(pid, command) for pid, command in found if pid != os.getpid()]


def kill_tree(pid: int) -> None:
    """End a process and everything under it (on Windows, its whole job). Never raises."""
    if WINDOWS:
        if pid in JOBS:
            _K32.TerminateJobObject(JOBS[pid], 1)
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)],
                           capture_output=True, check=False, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            pass
        return
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def group_members(pgid: int) -> list[tuple[int, str]]:
    """Every live process in one process group, by pid and command line."""
    if WINDOWS:
        if pgid not in JOBS:
            return windows_tree(pgid)
        pids = set(job_pids(JOBS[pgid])) - {os.getpid()}
        if not pids:
            return []
        commands = {row["ProcessId"]: _command(row) for row in windows_processes()}
        return [(pid, commands.get(pid, "")) for pid in sorted(pids)]
    out = subprocess.run(["ps", "-A", "-o", "pid=,pgid=,command="],
                         capture_output=True, text=True, check=False).stdout
    members = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        pid, group, command = parts
        if pid.isdigit() and group.isdigit() and int(group) == pgid and int(pid) != os.getpid():
            members.append((int(pid), command.strip()))
    return members


def sweep_group(pgid: int, grace: float = 1.0) -> list[tuple[int, str]]:
    """End everything still running in a run's process group, and report it.

    The harness kills the group when a deadline expires, but a child that
    backgrounds a server and then settles leaves it holding a port. That has
    happened: five servers from earlier runs were still listening hours later.
    """
    found = group_members(pgid)
    if not found:
        return []

    def signal_all(signal_number: int) -> None:
        if WINDOWS:
            if pgid in JOBS:
                _K32.TerminateJobObject(JOBS[pgid], 1)
            for pid, _ in group_members(pgid):
                kill_tree(pid)
            return
        # killpg is the right call, but a sandboxed or re-parented group can
        # refuse it, so fall back to each pid. The sweep must never raise.
        try:
            os.killpg(pgid, signal_number)
            return
        except OSError:
            pass
        for pid, _ in group_members(pgid):
            try:
                os.kill(pid, signal_number)
            except OSError:
                pass

    for signal_number in KILL_SIGNALS:
        signal_all(signal_number)
        deadline = time.monotonic() + grace
        while time.monotonic() < deadline:
            if not group_members(pgid):
                return found
            time.sleep(0.05)
    return found


def workspace_members(workspace: Path) -> list[tuple[int, str]]:
    """Every live process whose working directory is inside `workspace`."""
    root = os.path.realpath(workspace)
    if WINDOWS:
        # Windows does not expose another process's cwd; a server the model
        # left behind runs the workspace's .venv python or names a workspace path.
        needle = os.path.normcase(root)
        return [(row["ProcessId"], _command(row)) for row in windows_processes()
                if row["ProcessId"] != os.getpid()
                and needle in os.path.normcase(" ".join(
                    (row.get(key) or "").replace("/", "\\")
                    for key in ("ExecutablePath", "CommandLine")))]
    out = subprocess.run(["lsof", "-w", "-d", "cwd", "-F", "pn"],
                         capture_output=True, text=True, check=False).stdout
    pids, pid = [], None
    for line in out.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and pid is not None and pid != os.getpid():
            cwd = os.path.realpath(line[1:])
            if cwd == root or cwd.startswith(root + os.sep):
                pids.append(pid)
    if not pids:
        return []
    listed = subprocess.run(["ps", "-o", "pid=,command=", "-p", ",".join(map(str, pids))],
                            capture_output=True, text=True, check=False).stdout
    members = []
    for line in listed.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            members.append((int(parts[0]), parts[1].strip()))
    return members


def sweep_workspace(workspace: Path, grace: float = 1.0) -> list[tuple[int, str]]:
    """End every process still running inside a run's workspace, and report it.

    Pi's bash tool starts each command detached, in a session and process
    group of its own, so the group sweep never reaches a server the model
    started. Its working directory is the workspace, so that finds it. The
    sweep must never raise.
    """
    found = workspace_members(workspace)
    if not found:
        return []  # nothing left: skip the kill-and-recheck (each listing takes ~1 s on Windows)
    for signal_number in KILL_SIGNALS:
        for pid, _ in workspace_members(workspace):
            if WINDOWS:
                kill_tree(pid)
                continue
            try:
                os.kill(pid, signal_number)
            except OSError:
                pass
        deadline = time.monotonic() + grace
        while time.monotonic() < deadline:
            if not workspace_members(workspace):
                return found
            time.sleep(0.05)
    return found


def machine_label() -> str:
    """What this run ran on: enough to tell an M1 Pro from an M5 Max.

    Peak token counts travel between machines; walls do not.
    """
    brand = memory = ""
    try:
        brand = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                               capture_output=True, text=True, check=False).stdout.strip()
        memory = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        pass
    if not brand:
        brand = f"{platform.system()} {platform.machine()}"
    ram = f", {int(memory) // (1024 ** 3)} GiB" if memory.isdigit() else ""
    return f"{brand}{ram}"


def file_hashes(root: Path) -> dict[str, str]:
    """Every file under root by relative posix path, with its sha256."""
    hashes: dict[str, str] = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        try:
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
    return hashes


def _matches(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def layout_report(root: Path, pristine: dict[str, str],
                  layout: dict) -> dict:
    """What the run created or modified, and which of it the layout does not allow.

    A run can pass every hidden test and still write files the project did not
    ask for. This is the check for that, and it is deliberately about paths, not
    behaviour: allowed patterns and ignored artefacts come from the suite.
    """
    now = file_hashes(root)
    allow = list(layout.get("allow") or [])
    ignore = list(layout.get("ignore") or [])
    created = sorted(p for p in set(now) - set(pristine)
                     if not _matches(p, ignore))
    modified = sorted(p for p in now
                      if p in pristine and now[p] != pristine[p]
                      and not _matches(p, ignore))
    deleted = sorted(p for p in set(pristine) - set(now) if not _matches(p, ignore))
    outside = sorted(p for p in created + modified + deleted if not _matches(p, allow))
    return {"created": created, "modified": modified, "deleted": deleted, "out_of_layout": outside}


def resolve_pi_binary(pi_binary: str) -> str:
    """Pi runs with the workspace as its cwd, so a --pi-binary given as a relative path is made
    absolute here; a bare command name such as `pi` is left for PATH lookup."""
    if os.sep in pi_binary or (os.altsep and os.altsep in pi_binary):
        return str(Path(pi_binary).resolve())
    return pi_binary


def resolve_extras(remedy: str | None, extensions: list[Path]) -> tuple[list[str], list[Path]]:
    """The remedy units (`--remedy`, names or `preset:<name>`) and a learner's own extensions
    (`--extension`), as (unit names, files to load in order). Unknown names are refused."""
    names: list[str] = []
    for item in (remedy or "").split(","):
        item = item.strip()
        if not item:
            continue
        if item.startswith("preset:"):
            preset = REMEDIES / "presets" / f"{item.removeprefix('preset:')}.json"
            if not preset.is_file():
                known = sorted(f"preset:{q.stem}" for q in (REMEDIES / "presets").glob("*.json"))
                raise SystemExit(f"no preset {item!r}; known: {', '.join(known)}")
            names += json.loads(preset.read_text())
        else:
            names.append(item)
    paths: list[Path] = []
    for name in names:
        path = REMEDIES / f"{name}.ts"
        if not path.is_file():
            # as_posix: unit names use "/" on every OS (guard/repeat-loops, not guard\repeat-loops)
            known = sorted(q.relative_to(REMEDIES).with_suffix("").as_posix()
                           for q in REMEDIES.glob("*/*.ts"))
            raise SystemExit(f"no remedy unit {name!r}; known: {', '.join(known)}")
        paths.append(path)
    for path in extensions:
        if not Path(path).is_file():
            raise SystemExit(f"no extension file {path}")
        paths.append(Path(path).resolve())
    return names, paths


def extension_record(paths: list[Path]) -> list[dict]:
    """Each loaded file and its SHA-256, so a record says exactly what ran."""
    return [{"path": str(p), "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()}
            for p in paths]


def pi_argv(
    pi_binary: str,
    profile: Path,
    recorder: Path,
    provider: str,
    model: str,
    prompt: str,
    *,
    extension: Path | None = None,
    session_id: str | None = None,
    session_dir: Path | None = None,
    extras: list[Path] = (),
    context_files: bool = False,
) -> list[str]:
    # The default run is cold: --no-context-files drops the workspace's own AGENTS.md too.
    # context_files=True keeps it (warm), so a run can measure what the suite's AGENTS.md is worth.
    flags = [f for f in FLAGS if f != "--no-context-files"] if context_files else FLAGS
    session = (
        ["--session-id", session_id, "--session-dir", str(session_dir)]
        if session_id and session_dir
        else []
    )
    extra = ["-e", str(extension)] if extension is not None else []
    for path in extras:
        extra += ["-e", str(path)]
    # The recorder goes last: Pi runs before_provider_request handlers in load
    # order and each may replace the payload, so a recorder placed first would
    # log the messages before the worker appends its facts block. The cost is
    # that a compaction the worker refuses is not visible from here.
    return [
        pi_binary, *flags, "--provider", provider, "--model", model,
        *session, *extra, "-e", str(recorder), prompt,
    ]


def load_variant(suite: Suite, name: str) -> Path:
    """A suite's optional spec variant: prompts plus a workspace overlay."""
    if suite.root is None:
        raise SystemExit(f"suite {suite.name} has no root")
    variants = Path(suite.root) / "spec-variants"
    variant = variants / name
    if not variant.is_dir():
        available = sorted(p.name for p in variants.iterdir() if p.is_dir()) \
            if variants.is_dir() else []
        raise SystemExit(
            f"no spec variant {name!r} in {variants}; "
            f"available: {', '.join(available) or 'none'}")
    return variant


def open_tool_call(trace_lines, now: float) -> tuple[float, str] | None:
    """The oldest tool call still waiting for its result: (seconds open, command).

    A foreground server never returns, so its call stays open; a stall cutoff
    reads this to end the session instead of waiting out the whole deadline.
    """
    pending: list[dict] = []
    for line in trace_lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("type") == "tool_call":
            pending.append(row)
        elif row.get("type") == "tool_result" and pending:
            pending.pop(0)
    if not pending:
        return None
    call = pending[0]
    opened = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00")).timestamp()
    command = (call.get("input") or {}).get("command") or call.get("toolName", "")
    return round(now - opened, 1), command


def run_suite(
    suite: Suite,
    *,
    runs_dir: Path,
    arm: str = "bare",
    profile: Path = PROFILE,
    pi_binary: str = "pi",
    deadline: float | None = None,
    stall: float | None = None,
    single_prompt: bool = False,
    specs: str | None = None,
    extras: list[Path] = (),
    context_files: bool = False,
    budget: dict | None = None,
) -> Path:
    taken = guarded_listeners(GUARDED_PORTS)
    if taken:
        named = ", ".join(f"port {row['port']} (pid {row['pid']}, {row['command']})" for row in taken)
        raise SystemExit(f"a server is already listening on {named}; stop it and rerun "
                         "(no session was started)")
    run = new_run(runs_dir, suite.name)
    workspace = run / "workspace"
    workspace.mkdir()
    shutil.copytree(profile, run / "profile")
    recorder = run / "record-pi.mjs"
    shutil.copy2(RECORDER, recorder)
    if suite.root is not None and (suite.root / "base").is_dir():
        shutil.copytree(suite.root / "base", workspace, dirs_exist_ok=True)
    if suite.start is not None:
        shutil.copytree(suite.start, workspace, dirs_exist_ok=True)
    prompts = list(suite.prompts)
    if specs is not None:
        variant = load_variant(suite, specs)
        for path in sorted(variant.rglob("*")):
            rel = path.relative_to(variant)
            if rel.parts[0] == "prompts" or rel.name == "delete.json":
                continue
            target = workspace / rel
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        deletions = variant / "delete.json"
        if deletions.is_file():
            for rel in json.loads(deletions.read_text()):
                (workspace / rel).unlink(missing_ok=True)
        prompts = [_read_prompt(path)
                   for path in sorted((variant / "prompts").glob("*.md"))]
    pristine = file_hashes(workspace) if suite.layout is not None else None
    (run / 'brief.json').write_text(json.dumps({'variant': specs}) + '\n')
    prompts = (["\n\n".join(prompts)] if single_prompt else list(prompts))
    (run / "prompt.txt").write_text("\n\n".join(prompts) + "\n")
    trace = run / "trace.jsonl"
    trace.touch()
    sessions = run / "sessions"
    sessions.mkdir()
    provider, model = profile_pin(profile)
    # Record the pinned model so run.json (assembled later, out of this scope) and the
    # scoreboard can name which model produced the run.
    (run / "model.txt").write_text(f"{provider}/{model}\n")
    session_id = str(uuid.uuid4())
    settings = arm_settings(arm)
    env = {
        **os.environ,
        "PI_CODING_AGENT_DIR": str(run / "profile"),
        "MELLUM_TRACE_FILE": str(trace),
    }
    # Without the harness venv on PATH; without VIRTUAL_ENV, else uv warns in the workspace venv.
    env["PATH"] = session_path(env.get("PATH", ""), env.pop("VIRTUAL_ENV", None))
    for key in ARM_ENV_KEYS:
        env.pop(key, None)
    env.update(settings["env"])
    # With a budget, wall time is only a hang-guard: a run that hits it is censored (F.5).
    timeout_reason, budget_log, proxy = "deadline", None, None
    if budget is not None:
        # An explicit deadline keeps its meaning (an uncounted run's --deadline); otherwise the
        # suite's hang-guard applies, and a run it ends is censored.
        if deadline is None:
            deadline, timeout_reason = budget["wall_safety_seconds"], "wall_safety"
        budget_log = run / "proxy.jsonl"
        (run / "budget-limits.json").write_text(json.dumps(budget, indent=2) + "\n")
    started = time.monotonic()
    groups: list[int] = []
    leaked: list[dict] = []
    # The budget is the time the Pi processes ran, measured here, never the span of
    # trace rows: a hang writes no rows, so the trace undercounts it.
    child = None
    elapsed = 0.0
    termination_reason = "error"
    # The sweep runs however the loop ends, including a SIGTERM (main turns it
    # into SystemExit): a stopped run must still end the servers it started.
    try:
        if budget is not None:
            # Inside the try, so a stop from here on still ends the proxy in the finally.
            models_file = run / "profile" / "models.json"
            models = json.loads(models_file.read_text())
            target, suffix = proxy_target(models["providers"][provider]["baseUrl"])
        if budget is not None and not is_loopback(target):
            # The proxy forwards to loopback only. An uncounted run on another host (a LAN
            # profile) goes without it, bounded by the hang-guard alone, and says so.
            note = f"budget not enforced: the proxy is loopback-only and the profile targets {target}"
            (run / "budget-unenforced").write_text(note + "\n")
            (run / "budget-limits.json").unlink()
            print(f"warning: {note}", file=sys.stderr)
        elif budget is not None:
            proxy, port = start_budget_proxy(budget, target, budget_log)
            (run / "proxy.json").write_text(json.dumps({"pid": proxy.pid, "port": port, "target": target}) + "\n")
            models["providers"][provider]["baseUrl"] = f"http://127.0.0.1:{port}{suffix}"
            models_file.write_text(json.dumps(models, indent=2) + "\n")
            started = time.monotonic()
        for prompt in prompts:
            remaining = None if deadline is None else deadline - (time.monotonic() - started)
            if remaining is not None and remaining <= 0:
                (run / timeout_reason).write_text("hit\n")
                termination_reason = timeout_reason
                break
            # The spec-derived contract scopes itself to the phase this prompt names.
            env["ACCEPTANCE_PROMPT"] = prompt
            argv = pi_argv(
                pi_binary, run / "profile", recorder, provider, model, prompt,
                extension=settings["extension"],
                session_id=session_id, session_dir=sessions, extras=extras,
                context_files=context_files,
            )
            try:
                # No stdin: Pi with -p appends piped stdin to its prompt.
                child_started = time.monotonic()
                child = start_child(argv, cwd=workspace, env=env, stdin=subprocess.DEVNULL)
                groups.append(child.pid)
            except FileNotFoundError:
                raise SystemExit(f"pi not found: {pi_binary}; install Pi before running a suite")
            try:
                ended = wait_or_stall(child, run, trace, remaining, stall,
                                      budget_log=budget_log, timeout_reason=timeout_reason)
            finally:
                elapsed += time.monotonic() - child_started
            termination_reason = ended or "exited"
            if ended:
                break
    finally:
        if proxy is not None:
            stop_budget_proxy(proxy)
        for pgid in groups:
            leaked.extend({"pid": pid, "pgid": pgid, "command": command}
                          for pid, command in sweep_group(pgid))
        swept = {entry["pid"] for entry in leaked}
        leaked.extend({"pid": pid, "pgid": None, "command": command}
                      for pid, command in sweep_workspace(workspace) if pid not in swept)
        (run / "execution.json").write_text(json.dumps({
            "elapsed_seconds": round(elapsed, 3),
            "exit_code": child.poll() if child is not None else None,
            "termination_reason": termination_reason,
            "cleanup_ok": not any(group_members(pgid) for pgid in groups)
                          and not workspace_members(workspace),
        }, indent=2) + "\n")
    (run / "leaked.json").write_text(json.dumps(leaked, indent=2) + "\n")
    if pristine is not None and suite.layout is not None:
        (run / "layout.json").write_text(
            json.dumps(layout_report(workspace, pristine, suite.layout), indent=2) + "\n")
    if grader_touched(run, suite):
        (run / "contaminated").write_text("grader touched\n")
    return run


def wait_or_stall(child, run: Path, trace: Path, remaining: float | None,
                  stall: float | None, *, budget_log: Path | None = None,
                  timeout_reason: str = "deadline") -> str | None:
    """Wait for one Pi child; end it at the deadline, when a command stalls, or on budget.

    Returns timeout_reason ("deadline" or "wall_safety"), "stalled" or "budget" when the
    session was ended, else None. A child that exits on its own after its budget was spent
    (Pi stops at the 429) still ends as "budget".
    """
    if stall is None and budget_log is None:
        try:
            child.wait(timeout=remaining)
            return None
        except subprocess.TimeoutExpired:
            reason = timeout_reason
    else:
        until = None if remaining is None else time.monotonic() + remaining
        reason = None
        while child.poll() is None:
            if until is not None and time.monotonic() >= until:
                reason = timeout_reason
                break
            if budget_exhausted(budget_log):
                reason = "budget"
                break
            open_call = (open_tool_call(trace.read_text().splitlines(), time.time())
                         if stall is not None else None)
            if open_call and open_call[0] >= stall:
                (run / "stalled").write_text(json.dumps(
                    {"seconds": open_call[0], "limit": stall, "command": open_call[1]}) + "\n")
                reason = "stalled"
                break
            time.sleep(0.25 if budget_log is not None else 1)
        if reason is None:
            return "budget" if budget_exhausted(budget_log) else None
    kill_tree(child.pid)
    child.wait()
    if reason in ("deadline", "wall_safety"):
        (run / reason).write_text("hit\n")
    return reason


def grader_touched(run: Path, suite: Suite) -> bool:
    if suite.canary is None:
        return False
    text = (Path(run) / "trace.jsonl").read_text(errors="ignore")
    return suite.canary in text or f"suites/{suite.name}" in text


def grade_env(workspace: Path) -> dict[str, str]:
    """A grader subprocess's environment: the workspace on PYTHONPATH, and no
    VIRTUAL_ENV — uv warns when it points at a venv other than the run's."""
    from grading import grade_env as trusted_env
    return trusted_env(workspace) | {"PYTHONPATH": str(workspace)}



def grade(workspace: Path, suite: Suite | None = None) -> list[tuple[str, bool, str]]:
    from grading import _application, _base
    with tempfile.TemporaryDirectory(prefix="mellum-quality-") as scratch:
        copy = Path(scratch) / "application"
        _application(Path(workspace), copy, _base(suite) if suite else None)
        return _grade_workspace(copy)


def _grade_workspace(workspace: Path) -> list[tuple[str, bool, str]]:
    workspace = Path(workspace)
    (workspace / "pyrefly.toml").write_text(
        'project-includes = [\n    "**/*.py",\n]\n'
        'project-excludes = [\n    "tests/**",\n]\n')
    def tool(name: str, *args: str) -> list[str]:
        if (workspace / "pyproject.toml").is_file():
            command = ["uv", "--no-config", "run", "--project", str(workspace)]
            if (workspace / "uv.lock").is_file():
                command.append("--frozen")
            return [*command, "--with", name, name, *args]
        return ["uv", "--no-config", "run", "--no-project", "--with", name, name, *args]

    commands = (
        ("ruff", tool("ruff", "check", "--isolated", "--select", "F,E9", "--extend-exclude", "tests", "--extend-exclude", "grader_tests", ".")),
        ("pyrefly", tool("pyrefly", "check", ".")),
        ("complexipy", tool("complexipy", "--max-complexity-allowed", "10",
                            "--exclude", "tests", "--exclude", "grader_tests", ".")),
    )
    results = []
    for name, command in commands:
        # The tools print UTF-8; Windows would decode it as its ANSI code page and lose the output.
        result = subprocess.run(
            command, cwd=workspace, capture_output=True, text=True, check=False,
            encoding="utf-8", errors="replace", env=grade_env(workspace),
        )
        output = [line for line in (result.stdout + result.stderr).splitlines()
                  if line.strip()]
        results.append((name, result.returncode == 0, output[0] if output else ""))
    return results


def qualify(suite: Suite) -> tuple[bool, dict[str, bool]]:
    if suite.root is None:
        raise SystemExit(f"suite {suite.name} has no root")
    results: dict[str, bool] = {}
    for name in ("known-good", "known-broken"):
        fixture = Path(suite.root) / "fixtures" / name
        if not fixture.is_dir():
            raise SystemExit(f"missing fixture: {fixture}")
        workspace = Path(tempfile.mkdtemp(prefix=f"mellum-{suite.name}-{name}-"))
        try:
            shutil.copytree(Path(suite.root) / "base", workspace, dirs_exist_ok=True)
            shutil.copytree(fixture, workspace, dirs_exist_ok=True)
            passed, _ = score_workspace(workspace, suite)
            results[name] = passed
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
    return results["known-good"] and not results["known-broken"], results


def _execution(run: Path) -> dict:
    """The run's execution.json (written by run_suite), or {} for a run without one."""
    path = Path(run) / "execution.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def execution_outcome(run: Path) -> dict:
    """How the session ended, apart from how good its artifact is.

    A deadline or a stall is what ended it; otherwise a non-zero exit or a last reply
    that errored is an error, and anything else settled. A leaked server is a separate
    fact (cleanup_ok, leaked): it does not turn a settled session into an error.
    """
    execution = _execution(run)
    rows = [json.loads(line) for line in (Path(run) / "trace.jsonl").read_text().splitlines()
            if line.strip()]
    replies = [row["message"] for row in rows if row.get("type") == "message_end"
               and (row.get("message") or {}).get("role") == "assistant"]
    reason = execution.get("termination_reason")
    if reason in ("deadline", "stalled", "budget", "wall_safety"):
        completion = reason
    elif (reason != "exited" or execution.get("exit_code") != 0
          or (replies and replies[-1].get("stopReason") in ("error", "aborted"))):
        completion = "error"
    else:
        completion = "settled"
    # A run the hang-guard ended is censored: reported apart, never averaged in (F.5).
    return {"completion": completion, "censored": completion == "wall_safety",
            "exit_code": execution.get("exit_code"), "cleanup_ok": execution.get("cleanup_ok")}


# A blocked tool call never reaches the recorder: the worker's guard stops the
# event chain first, so there is no tool_call row. What the trace does carry is
# the refusal as the model saw it, in a toolResult message. This phrase is that
# refusal's first sentence; the guard test pins it on the extension side.
SERVER_REFUSAL = "starts a server in the foreground"


def report(run: Path) -> dict:
    rows = [
        json.loads(line)
        for line in (Path(run) / "trace.jsonl").read_text().splitlines()
        if line.strip()
    ]
    final = ""
    inputs = []
    outputs = []
    empties: list[int] = []
    guard_blocks = 0
    turns = 0
    for index, row in enumerate(rows):
        if row.get("type") != "message_end":
            continue
        message = row.get("message") or {}
        usage = message.get("usage") or {}
        value = usage.get("input", usage.get("prompt_tokens"))
        if isinstance(value, (int, float)):
            # The context sent is the whole prompt: Pi's input leaves out the cached prefix.
            inputs.append(value + sum(usage.get(key) or 0 for key in ("cacheRead", "cacheWrite")))
        value = usage.get("output", usage.get("completion_tokens"))
        if isinstance(value, (int, float)):
            outputs.append(value)
        if (message.get("role") == "toolResult"
                and SERVER_REFUSAL in str(message.get("content"))):
            guard_blocks += 1
        if message.get("role") != "assistant":
            continue
        # A turn is a reply that came back; an errored or aborted one was only a request.
        if message.get("stopReason") not in ("error", "aborted"):
            turns += 1
        blocks = message.get("content") or []
        said = any(b.get("type") == "text" and (b.get("text") or "").strip()
                   for b in blocks)
        called = any(b.get("type") == "toolCall" for b in blocks)
        if not said and not called:
            empties.append(index)
            continue
        for block in blocks:
            if block.get("type") == "text" and block.get("text"):
                final = block["text"]
                break
    # A nudge continues a run: the empty turn is followed by another request in
    # the same Pi process. Medium and hard start one process per prompt, so an
    # empty turn that ends a prompt is an empty final, not a nudge, however many
    # requests the next prompt makes.
    starts = [index for index, row in enumerate(rows)
              if row.get("type") == "instance_start"]

    def segment_end(at: int) -> int:
        later = [start for start in starts if start > at]
        return later[0] if later else len(rows)

    continued = sum(
        any(later.get("type") == "provider_request"
            for later in rows[at + 1:segment_end(at)])
        for at in empties)
    return {
        "requests": sum(row.get("type") == "provider_request" for row in rows),
        "turns": turns,
        "tool_calls": sum(row.get("type") == "tool_call" for row in rows),
        "tool_errors": sum(
            row.get("type") == "tool_result" and row.get("isError") for row in rows),
        "final_reply": final,
        "context": max(inputs) if inputs else None,
        "output_tokens": sum(outputs) if outputs else None,
        # The Pi processes' own run time (execution.json); unknown without it.
        "wall": _execution(run).get("elapsed_seconds"),
        "nudges": continued,
        "empty_finals": len(empties) - continued,
        "guard_blocks": guard_blocks,
        # Assistant turns the model was sent back with its reasoning as <think>
        # text (a serving fault; the largest history in the session).
        "reasoning_as_text": max(
            (sum("<think>" in str(m.get("content") or "")
                 for m in (row.get("payload") or {}).get("messages") or []
                 if m.get("role") == "assistant")
             for row in rows if row.get("type") == "provider_request"),
            default=0),
        # Times Pi compacted a context that neared its window, losing detail.
        "compactions": sum(row.get("type") == "before_compact" for row in rows),
    }



def score(run: Path, suite: Suite) -> tuple[bool, str]:
    passed, tail, _, _ = score_details(run, suite)
    return passed, tail


def score_details(run: Path, suite: Suite) -> tuple[bool, str, list[str], bool]:
    from grading import evaluate
    selector = Path(run) / 'brief.json'
    variant = json.loads(selector.read_text()).get('variant') if selector.is_file() else None
    result = evaluate(Path(run) / 'workspace', suite, variant=variant)
    return result['passed'], result['tail'], result['missing'], result['checks_ran']


def check_groups(expected, missing) -> dict[str, dict[str, int]]:
    """Count the expected checks per grader module, missing and total."""
    groups: dict[str, dict[str, int]] = {}
    for test in expected:
        module = test.split("::")[0].rsplit("/", 1)[-1]
        groups.setdefault(module, {"missing": 0, "total": 0})["total"] += 1
    for test in missing:
        module = test.split("::")[0].rsplit("/", 1)[-1]
        groups[module]["missing"] += 1
    return groups


def score_workspace_details(
    workspace: Path, suite: Suite
) -> tuple[bool, str, list[str], bool]:
    from grading import evaluate
    result = evaluate(workspace, suite)
    return result['passed'], result['tail'], result['missing'], result['checks_ran']



def score_workspace(workspace: Path, suite: Suite) -> tuple[bool, str]:
    passed, tail, _missing, _ran = score_workspace_details(workspace, suite)
    return passed, tail


def _run_sessions(
    suite: Suite,
    *,
    runs_dir: Path,
    pi_binary: str,
    repeat: int,
    grade_run: bool,
    deadline: float | None,
    arm: str = "bare",
    single_prompt: bool = False,
    specs: str | None = None,
    profile: Path = PROFILE,
    stall: float | None = None,
    remedies: list[str] = (),
    extras: list[Path] = (),
    context_files: bool = False,
    budget: dict | None = None,
    host_card: dict | None = None,
) -> list[tuple]:
    results = []
    for _ in range(repeat):
        run_dir = run_suite(suite, runs_dir=runs_dir, pi_binary=pi_binary,
                            deadline=deadline, arm=arm,
                            single_prompt=single_prompt, specs=specs,
                            profile=profile, stall=stall, extras=extras,
                            context_files=context_files, budget=budget)
        grades = grade(run_dir / "workspace", suite=suite) if grade_run else []
        from grading import evaluate
        evaluation = evaluate(run_dir / 'workspace', suite, variant=specs)
        tests_passed = evaluation['hidden_passed']
        tail, missing, checks_ran = (evaluation['tail'], evaluation['missing'], evaluation['checks_ran'])
        project_tests = evaluation['project_tests']
        failed_checks = len(missing)
        quality_ok = all(
            ok for name, ok, _ in grades if name in {"ruff", "complexipy"}
        ) if grades else True
        contaminated = (run_dir / "contaminated").exists()
        metrics = report(run_dir)
        over = record_failures(metrics, suite.record)
        passed = tests_passed and project_tests["passed"] and quality_ok and not contaminated and not over
        leaked_file = run_dir / "leaked.json"
        if leaked_file.is_file():
            metrics["leaked"] = json.loads(leaked_file.read_text())
        layout_file = run_dir / "layout.json"
        if layout_file.is_file():
            metrics["out_of_layout"] = json.loads(layout_file.read_text())["out_of_layout"]
        model_file = run_dir / "model.txt"
        from grader_history import grader_identity
        record = {
            "grader": grader_identity(suite),
            "suite": suite.name,
            "arm": arm,
            "model": model_file.read_text().strip() if model_file.is_file() else None,
            "remedies": list(remedies),
            "extensions": extension_record(list(extras)),
            "single_prompt": single_prompt,
            "specs": specs,
            "strip_thinking": arm_settings(arm)["env"].get("MELLUM_STRIP_THINKING") == "1",
            "machine": machine_label(),
            "pi_version": pi_version(pi_binary),
            # A counted run passed the host gate; an uncounted one says so (F.5).
            "counted": host_card is not None,
            "host_card": host_card,
            "deadline": deadline if deadline is not None or not budget else budget["wall_safety_seconds"],
            "budget": budget_record(run_dir),
            "stall": stall,
            "stalled": (json.loads((run_dir / "stalled").read_text())
                        if (run_dir / "stalled").exists() else None),
            "passed": passed,
            "tests_passed": tests_passed,
            "quality_ok": quality_ok,
            "project_tests": project_tests,
            "hidden_reports": evaluation["hidden_reports"],
            "contaminated": contaminated,
            "failed_checks": failed_checks,
            "checks_ran": checks_ran,
            "missing_checks": missing,
            "check_groups": check_groups(suite.expected, missing),
            "record_failures": over,
            **{key: value for key, value in metrics.items()
               if key != "final_reply"},
            **execution_outcome(run_dir),
        }
        (run_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n")
        results.append((run_dir, passed, tail, grades, metrics,
                        tests_passed, quality_ok, contaminated))
    return results


def _print_task(
    suite: Suite, results: list[tuple], repeat: int
) -> int:
    for index, (run_dir, passed, tail, grades, counts, tests_passed,
                quality_ok, contaminated) in enumerate(results, 1):
        print(_line(suite, run_dir, passed, counts, repeat, index,
                    tests_passed, quality_ok, contaminated))
        _print_grades(grades)
        if not passed:
            print(tail, file=sys.stderr)
    ok = sum(1 for result in results if result[1])
    if repeat > 1:
        print(f"{suite.name}: {ok}/{repeat} sessions passed")
    return ok


def session_budget(suite: Suite, counted: bool, override: dict | None) -> dict | None:
    """Every run on a suite with a budget.json is held to it; an uncounted run may pass --budget instead.

    A counted run (one with --host-card) must have its suite's budget."""
    if counted and suite.budget is None:
        raise SystemExit(f"suite {suite.name} has no budget.json, so it cannot be a counted run")
    return override if override is not None else suite.budget


def run_suites(
    names: list[str],
    *,
    grader: str = "current",
    suites_dir: Path = SUITES,
    runs_dir: Path = RUNS,
    pi_binary: str = "pi",
    grade_run: bool = False,
    repeat: int = 1,
    deadline: float | None = 600,
    arm: str = "bare",
    single_prompt: bool = False,
    specs: str | None = None,
    profile: Path = PROFILE,
    stall: float | None = None,
    remedies: list[str] = (),
    extras: list[Path] = (),
    context_files: bool = False,
    counted: bool = False,
    budget: dict | None = None,
    host_card: dict | None = None,
) -> tuple[int, int]:
    # Run easiest first and hardest last, so a slow hard suite never blocks the
    # quicker ones; unknown suites keep alphabetical order after the known tiers.
    order = {"easy": 0, "medium": 1, "hard": 2}
    available = sorted(
        (
            path.name
            for path in Path(suites_dir).iterdir()
            if ((path / "grader").is_dir() or (path / "tests").is_dir())
            and ((path / "task.md").exists() or (path / "prompts").is_dir())
        ),
        key=lambda name: (order.get(name, len(order)), name),
    )
    if "all" in names:
        names = available
    missing = [name for name in names if name not in available]
    if missing:
        raise SystemExit(f"no suite named {', '.join(missing)} in {suites_dir}; "
                         f"available: {', '.join(available)}")
    suites_passed = sessions_passed = sessions_total = 0
    for name in names:
        from grader_history import select_grader
        suite = select_grader(load_suite(suites_dir, name), grader)
        results = _run_sessions(
            suite, runs_dir=runs_dir, pi_binary=pi_binary,
            repeat=repeat, grade_run=grade_run, deadline=deadline, arm=arm,
            single_prompt=single_prompt, specs=specs, profile=profile, stall=stall,
            remedies=remedies, extras=extras, context_files=context_files,
            budget=session_budget(suite, counted, budget), host_card=host_card,
        )
        sessions_passed += _print_task(suite, results, repeat)
        sessions_total += len(results)
        if all(result[1] for result in results):
            suites_passed += 1
    print(f"{suites_passed}/{len(names)} suites passed "
          f"({sessions_passed}/{sessions_total} sessions)")
    return suites_passed, len(names)


def _line(
    suite: Suite,
    run_dir: Path,
    passed: bool,
    counts: dict,
    repeat: int = 1,
    index: int = 1,
    tests_passed: bool = True,
    quality_ok: bool = True,
    contaminated: bool = False,
) -> str:
    tag = suite.name + (f" [{index}/{repeat}]" if repeat > 1 else "")
    n_text = f"n={repeat}; " if repeat == 1 else ""
    deadline = (" deadline" if (Path(run_dir) / "deadline").exists()
                else " stalled" if (Path(run_dir) / "stalled").exists() else "")
    label = "CONTAMINATED" if contaminated else ("PASS" if passed else "FAIL")
    notes = []
    if not quality_ok:
        notes.append("quality FAIL")
    if contaminated:
        notes.append("grader touched")
    note = ("; " + ", ".join(notes)) if notes else ""
    nudges = counts.get("nudges")
    fires = "" if nudges is None else f", {nudges} nudges"
    return (f"{tag}: {label} ({n_text}run {run_dir}; "
            f"{counts['requests']} requests, {counts['tool_calls']} tool calls, "
            f"{counts['tool_errors']} tool errors{fires}{deadline}{note})")


def _print_grades(grades: list[tuple[str, bool, str]]) -> None:
    for name, ok, detail in grades:
        label = "pyrefly (advisory)" if name == "pyrefly" else name
        print(f"{label}: {'PASS' if ok else 'FAIL'}" + (f" ({detail})" if not ok else ""))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one eval suite or all of them")
    qualify_p = sub.add_parser("qualify", help="prove a suite's grader both ways")
    qualify_p.add_argument("--suite", required=True)
    qualify_p.add_argument("--grader", default="current")
    run.add_argument("--grader", default="current", help="assertion bundle: current, bc5db20 or 16cf9f9^")
    qualify_p.add_argument("--suites-dir", type=Path, default=SUITES)
    run.add_argument("--suite", required=True, help="a suite name, or all")
    run.add_argument("--suites-dir", type=Path, default=SUITES)
    run.add_argument("--runs-dir", type=Path, default=RUNS)
    run.add_argument("--pi-binary", default="pi")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--grade", action="store_true")
    run.add_argument("--repeat", type=int, default=1)
    run.add_argument("--deadline", type=float, default=None,
                     help="seconds; not with --host-card (a counted run uses its suite's wall_safety)")
    run.add_argument("--host-card", type=Path, default=None, metavar="PATH",
                     help="a passing host card for the live server (conformance.py); makes the run counted")
    run.add_argument("--budget", type=Path, default=None, metavar="PATH",
                     help="a budget.json to use instead of the suite's; not with --host-card")
    run.add_argument("--arm", choices=ARMS, default="bare")
    run.add_argument("--remedy", default=None, metavar="LIST",
                     help="remedy units to load on top of the arm: comma-separated names "
                          "(guard/repeat-loops) or preset:<name>")
    run.add_argument("--extension", type=Path, action="append", default=[], metavar="PATH",
                     help="a Pi extension of your own to load (repeatable)")
    run.add_argument("--stall", type=float, default=None, metavar="SECONDS",
                     help="end a session as stalled when one tool call has run this long "
                          "with no result (a foreground server); off by default")
    run.add_argument("--profile", type=Path, default=PROFILE,
                     help="the Pi profile directory (models.json) the sessions use; "
                          "default the pinned llama.cpp profile")
    run.add_argument("--single-prompt", action="store_true",
                     help="send the suite's prompts as one brief instead of steps")
    run.add_argument("--context-files", action="store_true",
                     help="keep the workspace's own AGENTS.md (warm); off by default the run is "
                          "cold (--no-context-files strips it)")
    run.add_argument("--specs", metavar="VARIANT", default=None,
                     help="use one of the suite's spec variants (spec-variants/<name>): original, joined or split")
    return parser


def utf8_relaunch_argv(argv: list[str], utf8_mode: int) -> list[str] | None:
    """The command that reruns the harness in UTF-8 mode, or None when not needed.

    Traces, specs and records are UTF-8, but Windows reads files in its ANSI
    code page unless Python runs in UTF-8 mode.
    """
    if not WINDOWS or utf8_mode:
        return None
    return [sys.executable, "-X", "utf8", *argv]


def main(argv: list[str] | None = None) -> int:
    # A stopped run (SIGTERM, as /lesson sends) unwinds normally, so its sweep runs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    parser = build_parser()
    args = parser.parse_args(argv)
    from grader_history import select_grader

    if args.command == "qualify":
        suite = select_grader(load_suite(args.suites_dir, args.suite), args.grader)
        ok, results = qualify(suite)
        for name, passed in results.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
        print(f"{suite.name}: {'QUALIFIED' if ok else 'NOT QUALIFIED'}")
        return 0 if ok else 1

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    # A run is counted exactly when it has a host card (F.5); run.json says which it was.
    counted = args.host_card is not None
    if counted and (args.deadline is not None or args.budget is not None):
        parser.error("--deadline and --budget are not for a counted run; it uses its suite's budget")
    override = json.loads(Path(args.budget).read_text()) if args.budget is not None else None

    def counted_gate() -> dict | None:
        """The host gate for a counted run (F.5); None for an uncounted one."""
        if not counted:
            return None
        import conformance
        providers = json.loads((Path(args.profile) / "models.json").read_text())["providers"]
        target, _ = proxy_target(next(iter(providers.values()))["baseUrl"])
        if not is_loopback(target):
            raise SystemExit(f"a counted run needs the model server on 127.0.0.1, not {target}; "
                             "the budget proxy and the host gate are loopback-only")
        return host_gate(Path(args.host_card).resolve(), target.rstrip("/"), conformance.load_pins())
    remedies, extras = resolve_extras(args.remedy, args.extension)
    args.pi_binary = resolve_pi_binary(args.pi_binary)
    # Pi runs with the workspace as its cwd, so every path handed to it must be absolute.
    args.runs_dir = Path(args.runs_dir).resolve()
    inside = project_above(args.runs_dir)
    if inside is not None:
        message = (f"--runs-dir {args.runs_dir} is inside a project ({inside}); a session there "
                   "can reach its venv. Use a directory outside any project, such as the default.")
        if counted:
            raise SystemExit(message)
        print(f"warning (uncounted run): {message}", file=sys.stderr)
    args.profile = Path(args.profile).resolve()
    args.suites_dir = Path(args.suites_dir).resolve()
    if args.suite == "all":
        run_suites(["all"], grader=args.grader, suites_dir=args.suites_dir, runs_dir=args.runs_dir,
                   pi_binary=args.pi_binary, grade_run=args.grade,
                   repeat=args.repeat, deadline=args.deadline, arm=args.arm,
                   single_prompt=args.single_prompt, specs=args.specs,
                   profile=args.profile, stall=args.stall,
                   remedies=remedies, extras=extras, context_files=args.context_files,
                   counted=counted, budget=override, host_card=counted_gate())
        return 0

    suite = select_grader(load_suite(args.suites_dir, args.suite), args.grader)
    provider, model = profile_pin(args.profile)
    if args.dry_run:
        settings = arm_settings(args.arm)
        if args.specs:
            variant = load_variant(suite, args.specs)
            prompt = _read_prompt(sorted((variant / "prompts").glob("*.md"))[0])
        else:
            prompt = suite.prompt
        print(shlex.join(pi_argv(args.pi_binary, args.profile, RECORDER, provider,
                                 model, prompt,
                                 extension=settings["extension"], extras=extras,
                                 context_files=args.context_files)))
        return 0
    budget = session_budget(suite, counted, override)
    gate = counted_gate()
    results = _run_sessions(
        suite, runs_dir=args.runs_dir, pi_binary=args.pi_binary,
        repeat=args.repeat, grade_run=args.grade, deadline=args.deadline,
        arm=args.arm, single_prompt=args.single_prompt, specs=args.specs,
        profile=args.profile, stall=args.stall,
        remedies=remedies, extras=extras, context_files=args.context_files,
        budget=budget, host_card=gate,
    )
    _print_task(suite, results, args.repeat)
    return 0


if __name__ == "__main__":
    relaunch = utf8_relaunch_argv(sys.argv, sys.flags.utf8_mode)
    if relaunch is not None:
        # PYTHONUTF8 carries UTF-8 mode on to the grader subprocesses too.
        sys.exit(subprocess.run(relaunch, env={**os.environ, "PYTHONUTF8": "1"}).returncode)
    sys.exit(main())
