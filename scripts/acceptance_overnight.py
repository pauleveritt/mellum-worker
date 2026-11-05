"""Qualified local acceptance comparison. Explicit prepare/run/recover, no hosted resources."""
import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "learn/code"))
import baseline
import containment
import harness
from acceptance import AcceptancePackage
from acceptance_budget import reconcile, summarize
from acceptance_containment import check_snapshot

ORDER = ["selective", "gated"] * 20
LIMIT = 8 * 60 * 60
PACKAGE = REPO / "learn/code/acceptance/easy-phase1"
SELECTIVE = ["prompt/name-the-layout", "prompt/python-developer", "prompt/verify-the-spec",
             "guard/foreground-server", "context/trim-tool-output"]
STOP_REQUESTED = False
write_json = baseline.write_json


def freeze_files(paths: list[Path]) -> dict[str, str]:
    return {str(p.resolve()): baseline.sha256(p) for p in paths}


def verify_files(freeze: dict[str, str]):
    for path, digest in freeze.items():
        if not Path(path).is_file() or baseline.sha256(Path(path)) != digest:
            raise ValueError(f"frozen input changed: {path}")


def may_start(remaining: float) -> bool:
    return remaining >= 660


def decide(summary: dict) -> str:
    s, g = summary["selective"], summary["gated"]
    if any(row["n"] != 20 or not row["reconciled"] or row["output_per_usable"] is None for row in (s, g)):
        return "no_decision"
    return ("candidate" if g["usable"] >= 18 and g["usable"] >= s["usable"]
            and g["output_per_usable"] <= s["output_per_usable"] else "not_candidate")


def stop_owned(identity: dict | None) -> bool:
    if not identity or baseline.process_identity(identity["pid"]) != identity:
        return False
    os.kill(identity["pid"], signal.SIGTERM)
    until = time.monotonic() + 10
    while time.monotonic() < until and baseline.process_identity(identity["pid"]) == identity:
        time.sleep(.2)
    if baseline.process_identity(identity["pid"]) == identity:
        os.kill(identity["pid"], signal.SIGKILL)
    return True


def require_free_port():
    result = subprocess.run(["lsof", "-nP", "-iTCP:8002", "-sTCP:LISTEN"], capture_output=True, text=True)
    if result.stdout:
        raise ValueError("inference port 8002 occupied; refusing to replace another listener")


def now():
    return datetime.now(UTC).isoformat()


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def recover_owned(batch: Path):
    # These are host-created control locations; never recurse into exported artifacts.
    for arm in ("selective", "gated"):
        parent = batch / arm
        for control in parent.glob(".container-*"):
            for name in ("check-1", "check-2", "check-3", "final-check"):
                location = control / name
                for identity_path in location.glob(".grading-*/container.json"):
                    identity = json.loads(identity_path.read_text())
                    owner = identity["host_owner"]
                    if baseline.process_identity(owner["pid"]) == owner and owner["pid"] != os.getpid():
                        stop_owned(owner)
                containment.recover(location)
        for audit in parent.glob("audit-*"):
            for identity_path in audit.glob(".grading-*/container.json"):
                owner = json.loads(identity_path.read_text())["host_owner"]
                if baseline.process_identity(owner["pid"]) == owner and owner["pid"] != os.getpid():
                    stop_owned(owner)
            containment.recover(audit)
        containment.recover(parent)


def watchdog(batch: Path):
    owner = json.loads((batch / "server-owner.json").read_text())
    cutoff = owner["cutoff_epoch"]
    while time.time() < cutoff:
        if baseline.process_identity(owner["controller"]["pid"]) != owner["controller"]:
            break
        time.sleep(1)
    stop_owned(owner["server"])
    stop_owned(owner["controller"])
    recover_owned(batch)
    write_json(batch / "watchdog-shutdown.json", {"at": now(), "cutoff_epoch": cutoff})


def prepare(batch: Path):
    from acceptance_qualification import qualify
    from acceptance_runtime_qualification import qualify as runtime_qualify, qualify_compaction
    batch.mkdir(parents=True, exist_ok=True)
    with (batch / "build.log").open("w") as output:
        command = [sys.executable, str(REPO / "learn/code/containment.py"), "build"]
        subprocess.run(command, check=True, stdout=output, stderr=subprocess.STDOUT, timeout=900)
    image = (batch / "build.log").read_text().splitlines()[-1].strip()
    assert image.startswith("sha256:")
    (batch / "image-id.txt").write_text(image + "\n")
    boundary = __import__("containment_qualification").qualify(image, batch / "boundary")
    if not boundary["qualified"]:
        raise ValueError("containment qualification failed")
    if not qualify(image, batch / "checker")["qualified"]:
        raise ValueError("checker mutation qualification failed")
    if not runtime_qualify(image, batch / "interaction")["qualified"]:
        raise ValueError("actual Pi gate qualification failed")
    if not qualify_compaction(image, batch / "compaction")["qualified"]:
        raise ValueError("actual Pi compaction qualification failed")
    files = [REPO / path for path in containment.source_hashes()]
    files += [Path(__file__), *(PACKAGE / name for name, _ in AcceptancePackage.load(PACKAGE).files),
              harness.PROFILE / "models.json", harness.PROFILE / "settings.json",
              REPO / "runs/2026-11-04-local-controlled6/backend-config.json",
              REPO / "docs/superpowers/research/2026-11-04-protected-acceptance-protocol.md"]
    files += [p for p in (harness.SUITES / "easy").rglob("*") if p.is_file()
              and not any(part in containment.OMIT for part in p.parts)]
    package = AcceptancePackage.load(PACKAGE)
    write_json(batch / "prepared.json", {"qualified": True, "image": image,
        "package_sha256": package.digest, "freeze": freeze_files(files), "at": now(),
        "boundary": boundary["material"], "order": ORDER, "limits": {"task": 600, "stall": 180, "batch": LIMIT}})


def live(server, identity, argv, runtime):
    if server.poll() is not None or baseline.process_identity(server.pid) != identity:
        raise ValueError("owned inference process exited or changed identity")
    command = subprocess.check_output(["ps", "-p", str(server.pid), "-o", "command="], text=True).strip()
    if command != " ".join(argv):
        raise ValueError("inference argv drift")
    verify_files(runtime)
    props = baseline.read_json_url("http://127.0.0.1:8002", "/props")
    slots = baseline.read_json_url("http://127.0.0.1:8002", "/slots")
    if (props["build_info"] != "b11669-620d2225c" or len(slots) != 2
            or any(slot["n_ctx"] != 50176 or slot["is_processing"] for slot in slots)):
        raise ValueError("live backend configuration drift")
    return {"props": props, "slots": slots, "identity": identity}


def collect(batch: Path):
    global STOP_REQUESTED
    prepared = json.loads((batch / "prepared.json").read_text())
    verify_files(prepared["freeze"])
    if not prepared["qualified"] or prepared["order"] != ORDER:
        raise ValueError("unqualified or altered preparation")
    if (batch / "server-owner.json").exists():
        raise ValueError("batch already started; retain it and use a fresh batch for a new freeze")
    image = prepared["image"]
    containment.image_info(image)
    package = AcceptancePackage.load(PACKAGE)
    old = json.loads((REPO / "runs/2026-11-04-local-controlled6/backend-config.json").read_text())
    weights = REPO / "runs/2026-11-04-local-layout3" / old["model"]["file"]
    if baseline.sha256(weights) != old["model"]["sha256"]:
        raise ValueError("model weight hash mismatch")
    argv = old["server"]["argv"]
    argv[argv.index("-m") + 1] = str(weights)
    version = subprocess.check_output([argv[0], "--version"], stderr=subprocess.STDOUT, text=True)
    if "build 11669, commit 620d2225c" not in version:
        raise ValueError("llama.cpp revision mismatch")
    runtime = old["backend"]["runtime_sha256"]
    verify_files(runtime)
    require_free_port()
    profile = batch / "profile"; profile.mkdir()
    models = json.loads((harness.PROFILE / "models.json").read_text())
    models["providers"]["llamacpp"]["baseUrl"] = "http://127.0.0.1:8002/v1"
    write_json(profile / "models.json", models)
    shutil.copy2(harness.PROFILE / "settings.json", profile / "settings.json")
    profile_hashes = freeze_files(list(profile.iterdir()))
    log = (batch / "server.log").open("w")
    server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    identity = baseline.process_identity(server.pid)
    cutoff_at = time.monotonic() + LIMIT
    write_json(batch / "server-owner.json", {"server": identity, "controller": baseline.process_identity(os.getpid()),
        "argv": argv, "started_at": now(), "cutoff_epoch": time.time() + LIMIT})
    guardian = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--watchdog", str(batch.resolve())],
        start_new_session=True, stdout=(batch / "watchdog.log").open("w"), stderr=subprocess.STDOUT)
    records = []
    try:
        until = time.monotonic() + 240
        while True:
            if server.poll() is not None:
                raise ValueError("inference startup failed")
            try:
                if baseline.read_json_url("http://127.0.0.1:8002", "/health") == {"status": "ok"}:
                    break
            except SystemExit:
                pass
            if time.monotonic() > until:
                raise ValueError("backend startup timeout")
            time.sleep(1)
        backend = live(server, identity, argv, runtime)
        text = (batch / "server.log").read_text()
        if "MTL0    : Apple M5 Max" not in text or "MTL0 KV buffer size" not in text or "offloaded 29/29 layers to GPU" not in text:
            raise ValueError("full Metal offload not proven")
        write_json(batch / "backend-live.json", backend)
        write_json(batch / "backend-config.json", {**old, "collection": {"n_per_arm": 20, "concurrency": 1,
            "deadline_seconds": 600, "open_tool_cutoff_seconds": 180}, "ownership": str(batch / "server-owner.json")})
        # A short native generation proves this exact server/client path before counted tasks.
        from acceptance_live_probe import qualify as qualify_live
        if not qualify_live(image, profile, batch / "live-qualification"):
            raise ValueError("live native qualification failed")
        write_json(batch / "registration.json", {"at": now(), "order": ORDER, "prepared": prepared,
            "profile_hashes": profile_hashes, "backend": backend,
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()})
        for index, arm in enumerate(ORDER):
            if STOP_REQUESTED or not may_start(cutoff_at - time.monotonic()):
                break
            verify_files(prepared["freeze"]); verify_files(profile_hashes); live(server, identity, argv, runtime)
            names, extras = harness.resolve_extras(",".join(SELECTIVE + (["check/external-acceptance"] if arm == "gated" else [])), [])
            before = (batch / "server.log").stat().st_size
            write_json(batch / "status.json", {"state": "running", "completed": len(records), "index": index + 1, "arm": arm, "at": now()})
            result = harness._run_sessions(harness.load_suite(harness.SUITES, "easy"), runs_dir=batch / arm,
                pi_binary="/usr/local/bin/pi", repeat=1, grade_run=True, deadline=600, stall=180,
                arm="vanilla", profile=profile, grade_versions=prepared["boundary"]["runtime"]["checkers"],
                isolation_image=image, remedies=names, extras=extras, gate_package=PACKAGE if arm == "gated" else None)
            run = Path(result[0][0])
            record = json.loads((run / "run.json").read_text())
            with (batch / "server.log").open("rb") as source:
                source.seek(before); segment = source.read().decode(errors="replace")
            (run / "backend-segment.log").write_text(segment)
            control = Path(json.loads((run / "containment.json").read_text())["control"])
            journal = json.loads((run / "acceptance-journal.json").read_text()) if arm == "gated" else []
            budget = reconcile(segment, lines(control / "relay.jsonl"), lines(run / "trace.jsonl"), journal)
            if arm == "gated":
                acceptance = json.loads((run / "acceptance.json").read_text())["result"]
                gate_status = json.loads((run / "acceptance.json").read_text())["status"]
            else:
                elapsed = record["elapsed_seconds"]
                acceptance = check_snapshot(run / "workspace", package, image, batch / arm / ("audit-" + run.name), max(0, 600 - elapsed))
                gate_status = "control"
            layout = json.loads((run / "layout.json").read_text())
            usable = (acceptance["status"] == "pass" and record["checks_ran"]
                and record["checks_passed"] == record["checks_total"] and record["code_health"] == "pass"
                and record["completion"] == "settled" and not layout["out_of_layout"]
                and (arm != "gated" or gate_status == "accepted"))
            records.append({**record, "run": str(run), "comparison_arm": arm, "acceptance": acceptance,
                "gate_status": gate_status, "repairs": journal[-1]["repairs"] if journal else 0,
                "initial_acceptance": journal[0]["result"] if journal else acceptance,
                "usable": usable, "budget": budget})
            write_json(batch / "records.json", records)
            summary = {arm: summarize([r for r in records if r["comparison_arm"] == arm]) for arm in ("selective", "gated")}
            write_json(batch / "summary.json", summary)
            write_json(batch / "decision.json", {"decision": decide(summary), "at": now()})
            print(json.dumps({"completed": len(records), "arm": arm, "usable": usable, "gate": gate_status, "budget": budget}), flush=True)
            if gate_status in {"integrity_error", "checker_error"} or acceptance["status"] in {"integrity_error", "checker_error"}:
                raise ValueError("acceptance integrity/checker failure; collection stopped for review")
            if not record["cleanup_ok"] or record["instrumentation_error"]:
                raise ValueError("collection integrity failure")
        verify_files(prepared["freeze"]); live(server, identity, argv, runtime)
        if baseline.sha256(weights) != old["model"]["sha256"]:
            raise ValueError("weights changed")
        write_json(batch / "status.json", {"state": "complete" if len(records) == 40 else "incomplete",
            "completed": len(records), "at": now()})
    except BaseException as error:
        write_json(batch / "failure.json", {"type": type(error).__name__, "detail": str(error), "at": now()})
        raise
    finally:
        stop_owned(identity)
        server.wait(timeout=15)
        guardian.terminate(); guardian.wait(timeout=10)
        log.close()
        recover_owned(batch)
        listener = subprocess.run(["lsof", "-nP", "-iTCP:8002", "-sTCP:LISTEN"], capture_output=True, text=True).stdout
        write_json(batch / "shutdown.json", {"at": now(), "owned_server_stopped": server.poll() is not None,
            "server_exit_code": server.returncode, "listener_8002": listener, "guardian_stopped": guardian.poll() is not None})


def interrupted(_signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True
    raise KeyboardInterrupt("owned batch interrupted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["--prepare", "--run", "--recover", "--watchdog"])
    parser.add_argument("batch", type=Path)
    # Modes are option-looking for readability, but parsed as a positional choice.
    raw = sys.argv[1:]
    if len(raw) != 2 or raw[0] not in {"--prepare", "--run", "--recover", "--watchdog"}:
        parser.print_help(); raise SystemExit(2)
    mode, location = raw; batch = Path(location).resolve()
    if mode == "--watchdog":
        watchdog(batch)
    else:
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        if mode == "--prepare": prepare(batch)
        elif mode == "--run": collect(batch)
        else:
            ownership = json.loads((batch / "server-owner.json").read_text())
            if baseline.process_identity(ownership["controller"]["pid"]) == ownership["controller"]:
                raise ValueError("batch has an active controller")
            stop_owned(ownership["server"]); recover_owned(batch)
