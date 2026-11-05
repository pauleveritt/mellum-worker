"""The Vanilla floor on the portable rig (LC.39). Runs on the inference host itself; no Docker.

    uv run python scripts/floor_cohort.py prepare BATCH --prefix PREFIX
    uv run python scripts/floor_cohort.py host BATCH NAME --prefix PREFIX --endpoint URL --model GGUF
        --server-log LOG --provider P --region R --rental-id ID --price-per-hour X --threads N [--reference-ppl F]
    uv run python scripts/floor_cohort.py run BATCH NAME
    uv run python scripts/floor_cohort.py post-check BATCH NAME
    uv run python scripts/floor_cohort.py record-stop BATCH NAME RENTAL --state S --storage-billing yes|no
    uv run python scripts/floor_cohort.py report BATCH

The driver never calls a provider API: renting, stopping and terminating happen outside it,
through the Runpod MCP, on the user's yes (docs/superpowers/specs/2026-11-05-portable-floor-design.md).
Design and rules: that spec and docs/superpowers/research/2026-11-05-portable-floor-preregistration.md.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "learn/code"))
import conformance
import floor
import harness
import isolation
import rig
from acceptance_budget import reconcile

RELAY = REPO / "scripts/containment/relay.mjs"
FROZEN = ["scripts/rig/pins.json", "scripts/rig/ppl.txt", "scripts/containment/relay.mjs",
          "scripts/containment/probe.py", "scripts/containment/pytest_probe.py", "scripts/floor_cohort.py",
          "learn/code/harness.py", "learn/code/floor.py", "learn/code/isolation.py", "learn/code/conformance.py",
          "learn/code/acceptance_native.py", "learn/code/acceptance_budget.py", "learn/code/rig.py",
          "learn/code/record-pi.mjs", "learn/code/profile/models.json", "learn/code/profile/settings.json"]
STARTUP_PORTS = [8000]       # the suite app's documented port; the Mac preflight refuses to start while it is taken


def now() -> str:
    return datetime.now(UTC).isoformat()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze() -> dict:
    files = [REPO / p for p in FROZEN]
    package = REPO / "learn/code/acceptance/easy-phase1"
    files += sorted(p for p in package.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    files += sorted(p for p in (harness.SUITES / "easy").rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return {str(p.relative_to(REPO)): sha256(p) for p in files}


def verify_freeze(frozen: dict) -> None:
    current = {path: sha256(REPO / path) for path in frozen}
    if current != frozen:
        changed = sorted(path for path in frozen if current[path] != frozen[path])
        raise SystemExit(f"frozen inputs changed since prepare: {changed}")


def events(batch: Path) -> list[dict]:
    path = batch / "batch.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def append_event(batch: Path, event: dict) -> None:
    with (batch / "batch.jsonl").open("a") as log:
        log.write(json.dumps({**event, "at": now()}) + "\n")


def rentals(batch: Path, name: str) -> list[Path]:
    root = batch / "hosts" / name
    # By when conformance checked the rental, never by file mtime: post-check and record-stop rewrite cards.
    return sorted((p for p in root.iterdir() if (p / "host-card.json").is_file()),
                  key=lambda p: json.loads((p / "host-card.json").read_text()).get("checked_at", "")) \
        if root.is_dir() else []


def latest_rental(batch: Path, name: str) -> tuple[Path, dict, dict]:
    found = rentals(batch, name)
    if not found:
        raise SystemExit(f"host {name} has no host card; run `host` first")
    folder = found[-1]
    return folder, json.loads((folder / "host-card.json").read_text()), json.loads((folder / "host.json").read_text())


def traversable(path: Path) -> bool:
    """Whether a user other than the owner can reach path: every component needs o+x."""
    path = Path(path).absolute()
    return all(part.stat().st_mode & 0o001 for part in [*reversed(path.parents), path])


def hidden_files() -> list[Path]:
    """What the session must never read: the hidden tests and the acceptance checker."""
    suite = harness.load_suite(harness.SUITES, "easy")
    return [*(p for p in Path(suite.tests).rglob("*") if p.is_file()),
            REPO / "learn/code/acceptance/easy-phase1/checker.py"]


# --- prepare and host ------------------------------------------------------------------------

def prepare(batch: Path, prefix: str | None) -> dict:
    pins = rig.load_pins()
    boot = pins["bootstrap"]
    expected = {"node": boot["node"]["version"], "pi": boot["pi"].rsplit("@", 1)[-1], "uv": boot["uv"],
                "python": boot["python"]}
    found = rig.tool_versions(prefix)
    if found != expected:
        raise SystemExit(f"bootstrap tools are not as pinned: expected {expected}, found {found}")
    commit = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    prepared = {"at": now(), "commit": commit, "pins_digest": rig.pins_digest(pins), "tools": found,
                "freeze": freeze()}
    write_json(batch / "prepared.json", prepared)
    return prepared


def host(batch: Path, name: str, args) -> dict:
    pins = rig.load_pins()
    pod = args.provider != "local"
    folder = batch / "hosts" / name / args.rental_id
    config = {"name": name, "rental_id": args.rental_id, "prefix": args.prefix, "endpoint": args.endpoint.rstrip("/"),
              "model": args.model, "server_log": args.server_log, "pod": pod,
              "perplexity_binary": args.perplexity_binary or f"{args.prefix}/bin/llama-perplexity"}
    write_json(folder / "host.json", config)
    protected = [Path(args.server_log), batch / "prepared.json", Path.home() / ".ssh", *hidden_files()] if pod else []
    pids = [int(p) for p in args.pids.split(",")] if args.pids else []
    server_command = None
    if pids:
        import shlex
        command = subprocess.run(["ps", "-o", "command=", "-p", str(pids[0])], capture_output=True, text=True).stdout
        server_command = shlex.split(command.strip()) if command.strip() else None
    gpu = conformance.gpu_info() if pod else {"name": "metal"}
    return conformance.check(pins, config["endpoint"], perplexity_binary=Path(config["perplexity_binary"]),
                             model=Path(args.model), reference_ppl=args.reference_ppl, tolerance=args.tolerance,
                             host={"provider": args.provider, "region": args.region, "rental_id": args.rental_id,
                                   "price_per_hour": args.price_per_hour, "threads": args.threads, "gpu": args.gpu},
                             out=folder / "host-card.json", prefix=args.prefix,
                             session_user=rig.SESSION_USER if pod else None, protected=tuple(protected),
                             pids=tuple(pids), reference_template=args.reference_template, gpu=gpu,
                             server_command=server_command)


# --- one session -----------------------------------------------------------------------------

def start_proxy(config: dict, pins: dict, log: Path):
    node = f"{config['prefix']}/bin/node" if config.get("prefix") else "node"
    session = pins["session"]
    child = subprocess.Popen([node, str(RELAY), "proxy", "--listen", "0", "--target", config["endpoint"] + "/",
                              "--log", str(log), "--max-requests", str(session["max_requests"]),
                              "--max-output", str(session["max_output_tokens"]),
                              "--unknown-charge", str(session["unknown_usage_charge"])],
                             stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, start_new_session=True)
    until = time.monotonic() + 15
    while time.monotonic() < until:
        if log.is_file():
            for line in log.read_text().splitlines():
                row = json.loads(line)
                if row.get("boundary") == "ready":
                    return child, row["port"]
        if child.poll() is not None:
            break
        time.sleep(0.05)
    child.kill()
    raise SystemExit("budget proxy failed to start")


def session_profile(directory: Path, port: int) -> Path:
    directory.mkdir(parents=True)
    models = json.loads((harness.PROFILE / "models.json").read_text())
    for provider in models["providers"].values():
        provider["baseUrl"] = f"http://127.0.0.1:{port}/v1"
    write_json(directory / "models.json", models)
    shutil.copy2(harness.PROFILE / "settings.json", directory / "settings.json")
    return directory


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def run_one(batch: Path, name: str, config: dict, card: dict, pins: dict, index: int) -> dict:
    """Run, grade and judge one session on this host.

    Ownership (final review, Critical 1): the run root and root's accounting files stay root-owned;
    the session owns only what Pi writes, and is swept before anything is read back. Grading runs on
    a fresh copy owned by the grading user, and root assembles the record from root's own files.
    """
    pod, prefix = config["pod"], config["prefix"]
    if not pod:
        preflight = isolation.preflight_mac(STARTUP_PORTS)
        if not preflight["ok"]:
            raise SystemExit(f"Mac preflight found a listener the session needs: {preflight['listeners']}; "
                             "free it and rerun (no session was started)")
    elif not traversable(batch):
        raise SystemExit(f"{batch} is not traversable by {rig.SESSION_USER}; put the batch outside /root")
    sessions, grading = batch / name / "sessions", batch / name / "grading"
    for folder in (sessions, grading):
        folder.mkdir(parents=True, exist_ok=True)
        folder.chmod(0o711)
    work = Path(tempfile.mkdtemp(prefix="floor-session-", dir=batch / name))     # root-only: the proxy log lives here
    proxy_log = work / "proxy.jsonl"
    proxy, port = start_proxy(config, pins, proxy_log)
    server_log = Path(config["server_log"])
    offset = server_log.stat().st_size if server_log.is_file() else 0
    session = pins["session"]
    home = Path(f"/home/{rig.SESSION_USER}") if pod else Path.home()
    base_env = (rig.user_env(prefix, rig.SESSION_USER, home=str(home)) if pod
                else {**os.environ, "PATH": f"{prefix}/bin:{os.environ['PATH']}" if prefix else os.environ["PATH"]})
    load_start = os.getloadavg()
    try:
        run = harness.run_suite(harness.load_suite(harness.SUITES, "easy"), runs_dir=sessions, arm="vanilla",
                                profile=session_profile(work / "profile", port),
                                pi_binary=f"{prefix}/bin/pi" if prefix else "pi", stall=session["open_tool_seconds"],
                                user=rig.SESSION_USER if pod else None, budget_log=proxy_log,
                                wall_safety=session["wall_safety_seconds"], base_env=base_env)
    finally:
        proxy.terminate()
        try:
            proxy.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy.kill()
    sweep = isolation.sweep_user(rig.SESSION_USER) if pod else None      # before anything is read back
    execution = json.loads((run / "execution.json").read_text())
    if sweep is None:
        sweep = {"ok": bool(execution.get("cleanup_ok"))}
    shutil.copy2(proxy_log, run / "proxy.jsonl")
    with server_log.open("rb") as source:
        source.seek(offset)
        segment = source.read().decode(errors="replace")
    (run / "backend-segment.log").write_text(segment)
    budget = reconcile(segment, lines(run / "proxy.jsonl"), lines(run / "trace.jsonl"), [])
    write_json(run / "budget.json", budget)
    copy = grading / run.name
    shutil.copytree(run, copy, symlinks=True)
    python = rig.probe_python(prefix) if prefix else Path(sys.executable)
    if pod:
        rig.chown_tree(copy, rig.GRADE_USER)
        grade_env = rig.user_env(prefix, rig.GRADE_USER, home=f"/home/{rig.GRADE_USER}")
        subprocess.run([str(python), str(Path(__file__).resolve()), "_grade", str(copy), "--python", str(python)],
                       env=grade_env, check=False, timeout=1800, cwd="/", **rig.drop_privileges(rig.GRADE_USER))
        grade_sweep = isolation.sweep_user(rig.GRADE_USER)
        sweep = {**sweep, "ok": sweep["ok"] and grade_sweep["ok"], "grade": grade_sweep}
    else:
        grade(copy, uncontained=True, python=python)
    problems = collect_grades(copy, run)
    shutil.rmtree(copy, ignore_errors=True)
    record = floor.session_record(run, card)
    recovered = floor.transport_recovered(lines(run / "proxy.jsonl"), record["completion"] or "")
    state, reason = floor.validity(execution, budget, sweep, recovered, post_check="pending")
    if problems and state == "counted":
        state, reason = "invalid", "grading outputs refused: " + "; ".join(problems)
    shutil.rmtree(work, ignore_errors=True)
    return {"type": "session", "host": name, "rental_id": config["rental_id"], "run": str(run), "index": index,
            "state": state, "reason": reason, "record": record, "sweep_ok": sweep["ok"],
            "load": {"start": load_start, "end": os.getloadavg()}}


GRADE_OUTPUTS = {"run.json": True, "acceptance.json": True, "grade.json": False, "hidden-grade.json": False}


def collect_grades(copy: Path, run: Path) -> list[str]:
    """Bring the grading user's outputs into the root-owned run root, never through a symlink.

    Completion and timing come from root's own execution record, not from the grading copy."""
    problems = []
    for name, required in GRADE_OUTPUTS.items():
        source = copy / name
        if source.is_symlink():
            problems.append(f"{name} is a symlink")
            continue
        if not source.is_file():
            if required:
                problems.append(f"{name} is missing")
            continue
        descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as handle:
            (run / name).write_bytes(handle.read(16 * 1024 * 1024))
    if (run / "run.json").is_file():
        record = json.loads((run / "run.json").read_text())
        record.update(harness.execution_outcome(run))
        write_json(run / "run.json", record)
    return problems


def _acceptance(run: Path, uncontained: bool, python: Path | None = None) -> None:
    from acceptance import AcceptancePackage
    from acceptance_native import check_snapshot_native
    from acceptance_qualification import PACKAGE
    package = AcceptancePackage.load(PACKAGE)
    if package.digest != rig.load_pins()["acceptance_package_sha256"]:
        raise SystemExit("acceptance package is not the pinned package")
    result = check_snapshot_native(run / "workspace", package, run / "acceptance-control", package.timeout,
                                   user=None, python=python or Path(sys.executable), env=dict(os.environ),
                                   uncontained=uncontained)
    write_json(run / "acceptance.json", {"status": "control", "result": result})


def grade(run: Path, *, uncontained: bool, python: Path | None = None) -> None:
    """Acceptance audit on the pristine tree, then hidden grading; on a pod this runs as the grading user."""
    pins = rig.load_pins()
    _acceptance(run, uncontained, python=python)
    harness.grade_and_record(run, harness.load_suite(harness.SUITES, "easy"), grade_run=True,
                             grade_versions=pins["bootstrap"]["checkers"], arm="vanilla", deadline=None,
                             stall=pins["session"]["open_tool_seconds"])


# --- the cohort ------------------------------------------------------------------------------

def run(batch: Path, name: str) -> None:
    pins = rig.load_pins()
    prepared = json.loads((batch / "prepared.json").read_text())
    if prepared["pins_digest"] != rig.pins_digest(pins):
        raise SystemExit("pin card changed since prepare")
    if name not in floor.PLAN:
        raise SystemExit(f"unknown host {name}; the plan is {floor.PLAN}")
    folder, card, config = latest_rental(batch, name)
    usable, reason = floor.card_usable(card, pins)
    if not usable:
        raise SystemExit(f"host {name} rental {card.get('rental_id')}: {reason} (conformance)")
    if any(e["type"] == "host_stopped" and e["host"] == name for e in events(batch)):
        return
    while True:
        mine = [e for e in events(batch) if e["type"] == "session" and e["host"] == name]
        counted = sum(e["state"] == "counted" for e in mine)
        invalid = sum(e["state"] == "invalid" for e in mine)
        if counted >= floor.PLAN[name]:
            return
        if prepared.get("freeze"):
            verify_freeze(prepared["freeze"])
        event = {**run_one(batch, name, config, card, pins, len(mine) + 1), "index": len(mine) + 1}
        append_event(batch, event)
        if event["state"] == "invalid" and not floor.may_replace({"replacements": invalid}):
            append_event(batch, {"type": "host_stopped", "host": name,
                                 "reason": f"{invalid + 1} invalid sessions exceed {floor.MAX_REPLACEMENTS} replacements"})
            return


def post_check(batch: Path, name: str) -> dict:
    folder, card, config = latest_rental(batch, name)
    result = conformance.post_check(rig.load_pins(), config["endpoint"], model=Path(config["model"]),
                                    prefix=config["prefix"])
    card["post_check"] = "passed" if result["passed"] else "failed"
    card["post_check_detail"] = result
    write_json(folder / "host-card.json", card)
    return card


def record_stop(batch: Path, name: str, rental: str, *, state: str, storage_billing: bool) -> dict:
    path = batch / "hosts" / name / rental / "host-card.json"
    card = json.loads(path.read_text())
    card["stopped"] = {"state": state, "storage_billing": storage_billing, "recorded_at": now()}
    write_json(path, card)
    return card


def report(batch: Path) -> dict:
    cards = {}
    for name in floor.PLAN:
        for folder in rentals(batch, name):
            cards[(name, folder.name)] = json.loads((folder / "host-card.json").read_text())
    records, excluded = [], []
    for event in events(batch):
        if event["type"] != "session":
            continue
        post = cards.get((event["host"], event["rental_id"]), {}).get("post_check")
        if event["state"] != "counted" or post == "failed":
            excluded.append({"host": event["host"], "rental_id": event["rental_id"], "index": event.get("index"),
                             "run": event.get("run"), "reason": event["reason"] if event["state"] != "counted"
                             else "host failed the post-cohort conformance check"})
            continue
        reason = "post-check unavailable" if post is None else event["reason"]
        records.append({**event["record"], "host": event["host"], "rental_id": event["rental_id"],
                        "run": event["run"], "validity_reason": reason})
    summary = floor.summarize_floor(records)
    a = [r for r in records if r["host"] == "A"]
    b = [r for r in records if r["host"] == "B"]
    portability = (floor.portability(a, b) if a and b else
                   {"portable": None, "reasons": ["needs counted sessions on both CUDA hosts"]})
    write_json(batch / "records.json", records)
    write_json(batch / "excluded.json", excluded)
    write_json(batch / "summary.json", summary)
    write_json(batch / "portability.json", portability)
    (batch / "scorecard.md").write_text(scorecard(summary, records, portability, excluded))
    return summary


def scorecard(summary: dict, records: list[dict], portability: dict, excluded: list[dict] = ()) -> str:
    def table(title, rows, row_summary):
        low, high = row_summary["wilson_95"]
        checks = sorted({name for r in rows for name in r.get("acceptance_checks", {})})
        out = [f"## {title}", "", f"Usable {row_summary['usable']}/{row_summary['n']} "
               f"(Wilson 95% {low:.2f}–{high:.2f}){' · uncontained' if row_summary['uncontained'] else ''}", "",
               "| Measure | Passed |", "| --- | ---: |",
               f"| Hidden all-pass | {sum(r.get('hidden_all_pass') is True for r in rows)}/{len(rows)} |",
               f"| Settled | {sum(r.get('completion') == 'settled' for r in rows)}/{len(rows)} |",
               f"| Budget endings | {sum(r.get('completion') == 'budget' for r in rows)}/{len(rows)} |"]
        out += [f"| Acceptance: {name} | {sum(r['acceptance_checks'].get(name) is True for r in rows)}/{len(rows)} |"
                for name in checks]
        return "\n".join(out) + "\n"
    parts = ["# Vanilla floor scorecard", ""]
    for name, row_summary in summary["per_host"].items():
        parts.append(table(f"Host {name}", [r for r in records if r["host"] == name], row_summary))
    parts.append(table("Pooled A+B", [r for r in records if r["host"] in floor.CUDA_HOSTS], summary["pooled_cuda"]))
    parts.append(table("Pooled A+B+M", records, summary["pooled_all"]))
    endings = [r for r in records if r.get("completion") == "budget"]
    parts.append("## Budget endings\n\n" + ("\n".join(f"- Host {r['host']}: `{r['run']}`" for r in endings)
                                             or "None.") + "\n")
    parts.append("## Invalid sessions\n\n" + ("\n".join(f"- Host {e['host']} session {e['index']}: {e['reason']}"
                                                         f" (`{e['run']}`)" for e in excluded) or "None.") + "\n")
    verdict = {True: "pooling allowed", False: "not portable", None: "not yet readable"}[portability["portable"]]
    parts.append(f"## Portability\n\n{verdict}. {'; '.join(portability['reasons'])}\n")
    return "\n".join(parts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); p.add_argument("batch", type=Path); p.add_argument("--prefix")
    p = sub.add_parser("host"); p.add_argument("batch", type=Path); p.add_argument("name", choices=list(floor.PLAN))
    for flag in ("--endpoint", "--model", "--server-log", "--provider", "--region", "--rental-id"):
        p.add_argument(flag, required=True)
    p.add_argument("--prefix"); p.add_argument("--perplexity-binary"); p.add_argument("--gpu", default="")
    p.add_argument("--price-per-hour", type=float, default=0.0); p.add_argument("--threads", type=int, required=True)
    p.add_argument("--reference-ppl", type=float); p.add_argument("--tolerance", type=float, default=0.01)
    p.add_argument("--reference-template"); p.add_argument("--pids", default="")
    p = sub.add_parser("run"); p.add_argument("batch", type=Path); p.add_argument("name", choices=list(floor.PLAN))
    p = sub.add_parser("post-check"); p.add_argument("batch", type=Path); p.add_argument("name", choices=list(floor.PLAN))
    p = sub.add_parser("record-stop"); p.add_argument("batch", type=Path); p.add_argument("name")
    p.add_argument("rental"); p.add_argument("--state", required=True)
    p.add_argument("--storage-billing", choices=["yes", "no"], required=True)
    p = sub.add_parser("report"); p.add_argument("batch", type=Path)
    p = sub.add_parser("_grade"); p.add_argument("run", type=Path); p.add_argument("--python", type=Path)
    p.add_argument("--uncontained", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        args.batch.mkdir(parents=True, exist_ok=True); prepare(args.batch, args.prefix)
    elif args.command == "host":
        card = host(args.batch, args.name, args); print(json.dumps({"passed": card["passed"]}))
        return 0 if card["passed"] else 1
    elif args.command == "run":
        run(args.batch, args.name)
    elif args.command == "post-check":
        print(json.dumps({"post_check": post_check(args.batch, args.name)["post_check"]}))
    elif args.command == "record-stop":
        record_stop(args.batch, args.name, args.rental, state=args.state, storage_billing=args.storage_billing == "yes")
    elif args.command == "report":
        print(json.dumps(report(args.batch), indent=2))
    elif args.command == "_grade":
        grade(args.run, uncontained=args.uncontained, python=args.python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
