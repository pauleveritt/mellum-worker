"""Temporary Docker backend for tonight's measurements; never a native fallback."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts/containment"
LABEL = "mellum.measurement.owner"
OMIT = {".venv", "__pycache__", ".cache", "uv-cache", "node_modules"}


def agent_environment() -> dict[str, str]:
    return {"HOME": "/tmp/home", "UV_CACHE_DIR": "/tmp/uv-cache",
            "UV_PYTHON_INSTALL_DIR": "/opt/python", "UV_OFFLINE": "1",
            "PATH": "/usr/local/bin:/usr/bin:/bin", "TERM": "dumb"}


def create_argv(image: str, owner: str) -> list[str]:
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
        raise ValueError("a content-addressed image ID is required")
    return ["docker", "create", "--network", "none", "--read-only", "--user", "1000:1000",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "256", "--memory", "4g", "--cpus", "4",
            "--mount", f"type=volume,source=mellum-attempt-{owner},target=/attempt",
            "--tmpfs", "/tmp:rw,exec,nosuid,nodev,size=1g,uid=1000,gid=1000,mode=1777",
            "--label", f"{LABEL}={owner}", image, "sleep", "infinity"]


def docker(*args: str, **kwargs):
    kwargs.setdefault("timeout", 120)
    return subprocess.run(["docker", *args], check=True, **kwargs)


def volume_argv(owner: str) -> list[str]:
    # A tmpfs-backed named volume bounds scratch without the paused-export
    # limitation of Docker's direct --tmpfs mounts.
    return ["docker", "volume", "create", "--driver", "local", "--opt", "type=tmpfs",
            "--opt", "device=tmpfs", "--opt", "o=size=1g,uid=1000,gid=1000,mode=0700",
            "--label", f"{LABEL}={owner}", f"mellum-attempt-{owner}"]


def run_bounded_command(argv: list[str], *, timeout: float, **kwargs):
    """The trusted host enforces this even if all container processes stop."""
    if timeout is None or timeout <= 0:
        raise ValueError("a positive host watchdog timeout is required")
    return subprocess.run(argv, timeout=timeout, **kwargs)


def extract_regular(stream, destination: Path, *, max_bytes=512 * 1024**2, max_members=30000):
    """Materialize untrusted tar into a fresh staging directory, without links."""
    destination.mkdir(parents=True, exist_ok=False)
    seen, size = set(), 0
    with tarfile.open(fileobj=stream, mode="r|*") as archive:
        for count, item in enumerate(archive, 1):
            path = PurePosixPath(item.name)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError("unsafe export path")
            if count > max_members:
                raise ValueError("export member limit exceeded")
            if any(part in OMIT for part in path.parts):
                continue
            if not (item.isdir() or item.isreg()) or str(path) in seen:
                raise ValueError("export contains link, special file or duplicate")
            seen.add(str(path))
            size += item.size
            if size > max_bytes:
                raise ValueError("export byte limit exceeded")
            target = destination.joinpath(*path.parts)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if item.isdir():
                    target.mkdir(exist_ok=True)
                else:
                    with archive.extractfile(item) as source, target.open("xb") as output:
                        shutil.copyfileobj(source, output, length=65536)
            except OSError as error:
                raise ValueError("export path collision") from error


def source_hashes() -> dict:
    paths = [*SCRIPTS.glob("*"), *(REPO / "learn/code").glob("containment*.py"),
             REPO / "learn/code/harness.py", REPO / "learn/code/baseline.py",
             *(REPO / "learn/code").glob("acceptance*.py"),
             * (REPO / "extensions").rglob("*.ts"),
             *(p for p in (REPO / "remedies").rglob("*") if p.is_file()),
             REPO / "learn/code/suites/easy/base/pyproject.toml",
             REPO / "learn/code/suites/easy/base/uv.lock"]
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


def image_instrument_sources() -> list[Path]:
    return [REPO / "learn/code" / name for name in (
        "harness.py", "baseline.py", "containment.py", "acceptance.py",
        "acceptance_containment.py", "acceptance_probe.py")]


def build_image() -> str:
    # A narrow, explicit context prevents uploading runs, credentials or graders.
    with tempfile.TemporaryDirectory(prefix="mellum-image-") as temporary:
        context = Path(temporary)
        shutil.copytree(SCRIPTS, context, dirs_exist_ok=True)
        shutil.copytree(REPO / "extensions", context / "instrument/extensions")
        shutil.copytree(REPO / "remedies", context / "instrument/remedies")
        for source in image_instrument_sources():
            target = context / "instrument/learn/code" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        deps = context / "dependencies"
        deps.mkdir()
        for name in ("pyproject.toml", "uv.lock"):
            shutil.copy2(REPO / "learn/code/suites/easy/base" / name, deps / name)
        (context / "sources.json").write_text(json.dumps(source_hashes(), sort_keys=True))
        docker("build", "--iidfile", str(context / "image-id"), str(context), timeout=900)
        return (context / "image-id").read_text().strip()


class Container:
    def __init__(self, image: str, control: Path):
        self.image, self.control = image, control
        self.owner = uuid.uuid4().hex
        self.cid = None
        self.relay = None
        control.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        from baseline import write_json, process_identity
        create = create_argv(self.image, self.owner)
        # The unique label is durable before create: recovery can find even a
        # container created immediately before host SIGKILL, without trusting PIDs.
        self.identity = {"owner": self.owner, "image": self.image,
                         "host_owner": process_identity(os.getpid()), "policy": create,
                         "volume_policy": volume_argv(self.owner)}
        write_json(self.control / "container.json", self.identity)
        try:
            subprocess.run(volume_argv(self.owner), check=True, timeout=120, stdout=subprocess.DEVNULL)
            self.cid = subprocess.check_output(create, text=True).strip()
            self.identity["container_id"] = self.cid
            write_json(self.control / "container.json", self.identity)
            docker("start", self.cid, stdout=subprocess.DEVNULL)
            until = time.monotonic() + 60
            while subprocess.run(self.exec_argv("test", "-f", "/tmp/runtime-ready"),
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
                if time.monotonic() > until:
                    raise RuntimeError("contained runtime preparation timed out")
                time.sleep(.2)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def exec_argv(self, *args: str, user="1000:1000", env=None, interactive=False) -> list[str]:
        argv = ["docker", "exec", *(["-i"] if interactive else []), "--user", user]
        for key, value in (env or {}).items():
            argv += ["--env", f"{key}={value}"]
        return [*argv, self.cid, *map(str, args)]

    def execute(self, *args: str, **kwargs):
        return run_bounded_command(self.exec_argv(*args), timeout=kwargs.pop("timeout", 120), check=True, **kwargs)

    def seed(self, source: Path):
        # Docker's archive-write API rejects read-only rootfs even for tmpfs.
        # Extract trusted prepared inputs through exec into private scratch.
        with tempfile.TemporaryFile() as stream:
            with tarfile.open(fileobj=stream, mode="w") as archive:
                archive.add(source, arcname=".")
            stream.seek(0)
            docker("exec", "-i", "--user", "1000:1000", self.cid,
                   "tar", "-x", "--no-same-owner", "-C", "/attempt", stdin=stream)

    def start_relay(self, target: str):
        self.relay = subprocess.Popen(["node", str(SCRIPTS / "relay.mjs"), "host",
            self.cid, target, str(self.control / "relay.jsonl")],
            stdout=(self.control / "relay-output.txt").open("w"), stderr=subprocess.STDOUT)
        until = time.monotonic() + 30
        while time.monotonic() < until:
            log = self.control / "relay.jsonl"
            if log.exists() and '"boundary":"ready"' in log.read_text():
                return
            if self.relay.poll() is not None:
                break
            time.sleep(.1)
        raise RuntimeError("contained inference relay failed to start")

    def export(self, path: str, destination: Path, *, deadline_at: float | None = None):
        until = deadline_at if deadline_at is not None else time.monotonic() + 30
        def remaining():
            value = until - time.monotonic()
            if value <= 0:
                raise subprocess.TimeoutExpired("snapshot export", 0)
            return value
        docker("pause", self.cid, stdout=subprocess.DEVNULL, timeout=remaining())
        # Spool first: extracting a live pipe can block before a wait timeout.
        with tempfile.TemporaryFile() as archive:
            docker("cp", self.cid + ":" + path, "-", stdout=archive,
                   stderr=subprocess.PIPE, timeout=remaining())
            remaining(); archive.seek(0)
            extract_regular(archive, destination)
            remaining()

    def snapshot(self, path: str, destination: Path, *, deadline_at: float | None = None):
        try:
            self.export(path, destination, **({"deadline_at": deadline_at} if deadline_at is not None else {}))
        finally:
            docker("unpause", self.cid, stdout=subprocess.DEVNULL,
                   timeout=max(.01, min(3, deadline_at - time.monotonic())) if deadline_at is not None else 3)

    def __exit__(self, *_):
        if self.relay is not None:
            self.relay.terminate()
            try:
                self.relay.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.relay.kill()
                self.relay.wait()
        remove_owned(self.identity)
        from baseline import write_json
        write_json(self.control / "removed.json", {"removed": True})


def remove_owned(identity: dict):
    ids = docker("ps", "--all", "--quiet", "--no-trunc", "--filter",
                 f"label={LABEL}={identity['owner']}", capture_output=True, text=True).stdout.split()
    for cid in ids:
        actual = json.loads(docker("inspect", cid, capture_output=True, text=True).stdout)[0]
        if actual["Image"] != identity["image"] or actual["Config"]["Labels"].get(LABEL) != identity["owner"]:
            raise RuntimeError("container ownership mismatch")
        docker("rm", "--force", cid, stdout=subprocess.DEVNULL)
    volumes = docker("volume", "ls", "--quiet", "--filter",
                     f"label={LABEL}={identity['owner']}", capture_output=True, text=True).stdout.split()
    for volume in volumes:
        actual = json.loads(docker("volume", "inspect", volume, capture_output=True, text=True).stdout)[0]
        if (volume != f"mellum-attempt-{identity['owner']}"
                or actual["Labels"].get(LABEL) != identity["owner"]):
            raise RuntimeError("volume ownership mismatch")
        docker("volume", "rm", volume, stdout=subprocess.DEVNULL)


def preserve_owned(identity: dict, control: Path):
    """Best-effort bounded forensic export before deleting an orphan model task."""
    from baseline import write_json
    destination = control / "emergency-export"
    if destination.exists():
        return
    ids = docker("ps", "--all", "--quiet", "--no-trunc", "--filter",
                 f"label={LABEL}={identity['owner']}", capture_output=True, text=True).stdout.split()
    for cid in ids:
        actual = json.loads(docker("inspect", cid, capture_output=True, text=True).stdout)[0]
        if actual["Image"] != identity["image"] or actual["Config"]["Labels"].get(LABEL) != identity["owner"]:
            raise RuntimeError("container ownership mismatch")
        try:
            if actual["State"]["Running"] and not actual["State"]["Paused"]:
                docker("pause", cid, stdout=subprocess.DEVNULL, timeout=10)
            with tempfile.TemporaryFile() as archive:
                docker("cp", cid + ":/attempt/runs", "-", stdout=archive, stderr=subprocess.PIPE, timeout=30)
                archive.seek(0)
                extract_regular(archive, destination)
            write_json(control / "emergency-export.json", {"preserved": True})
        except (ValueError, RuntimeError, subprocess.SubprocessError) as error:
            write_json(control / "emergency-export.json", {"preserved": False, "error": str(error)})


def recover(root: Path):
    from baseline import process_identity, write_json
    # Only host-created controls at known orchestration levels have authority.
    # Never recursively discover JSON filenames inside exported model artifacts.
    parents = [root, *root.glob("*-easy-*/attempt-*")]
    controls = [p for parent in parents for pattern in (".container-*/container.json", ".grading-*/container.json")
                for p in parent.glob(pattern)]
    for control in controls:
        if (control.is_symlink() or control.parent.is_symlink()
                or not re.fullmatch(r"\.(?:container|grading)-[a-f0-9]{32}", control.parent.name)):
            raise RuntimeError("invalid host control directory")
        if (control.parent / "removed.json").exists():
            continue
        identity = json.loads(control.read_text())
        if (not re.fullmatch(r"[a-f0-9]{32}", identity.get("owner", ""))
                or not isinstance(identity.get("host_owner", {}).get("pid"), int)
                or not isinstance(identity.get("host_owner", {}).get("start"), str)
                or identity.get("volume_policy") != volume_argv(identity["owner"])
                or identity.get("policy") != create_argv(identity.get("image", ""), identity["owner"])):
            raise RuntimeError("invalid host control identity")
        owner = identity["host_owner"]
        if process_identity(owner["pid"]) == owner:
            raise RuntimeError("contained attempt has an active owner")
        if control.parent.name.startswith(".container-"):
            preserve_owned(identity, control.parent)
        remove_owned(identity)
        write_json(control.parent / "removed.json", {"removed": True, "recovered": True})


def image_info(image: str) -> dict:
    create_argv(image, "inspect")
    result = docker("run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges", "--entrypoint", "node", image,
                    "/opt/identity.mjs", capture_output=True, text=True)
    identity = json.loads(result.stdout)
    if identity["sources"] != source_hashes():
        raise SystemExit("containment image source inputs changed; rebuild image")
    if (identity["node"] != "v24.22.1" or identity["pi"]["version"] != "1.4.0"
            or identity["python"] != "3.14.2" or identity["uv"] != "0.11.6"):
        raise SystemExit("contained runtime version mismatch")
    engine = json.loads(docker("info", "--format", "{{json .}}", capture_output=True, text=True).stdout)
    return {"backend": "temporary-docker", "image": image, "runtime": identity,
            "engine": {k: engine[k] for k in ("ID", "ServerVersion", "OSType", "Architecture")},
            "policy": create_argv(image, "<ATTEMPT_OWNER>"),
            "volume_policy": volume_argv("<ATTEMPT_OWNER>")}


def suite_data(suite, *, grading=False) -> dict:
    data = {"name": suite.name, "prompts": suite.prompts,
            "layout": suite.layout, "record": suite.record}
    if grading:
        data.update(expected=suite.expected, canary=suite.canary)
    return data


def contained_extras(paths) -> list[str]:
    mapped = []
    for path in paths:
        path = Path(path).resolve()
        if not path.is_relative_to(REPO / "remedies") or path.suffix != ".ts" or not path.is_file():
            raise ValueError("contained extras must be repository remedy units")
        mapped.append(str(PurePosixPath("/opt/instrument") / path.relative_to(REPO)))
    return mapped


def run_contained(suite, *, image: str, runs_dir: Path, profile: Path,
                  inference_target="http://127.0.0.1:8002", **options) -> Path:
    from baseline import write_json
    from acceptance import AcceptancePackage, Gate
    from acceptance_containment import run_model_with_gate, check_snapshot, snapshot_digest
    protected = any(Path(p).name == "external-acceptance.ts" for p in options.get("extras", ()))
    package_path = options.pop("gate_package", None)
    audit_path = options.pop("audit_package", None)
    if protected != bool(package_path):
        raise ValueError("protected remedy and qualified external controller package must be enabled together")
    if protected and len(suite.prompts) != 1:
        raise ValueError("protected adapter supports one task per session")
    package = AcceptancePackage.load(package_path) if protected else None
    audit_package = AcceptancePackage.load(audit_path) if audit_path else None
    task_id = uuid.uuid4().hex
    run_name = "task-" + task_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    control = runs_dir / (".container-" + uuid.uuid4().hex)
    with tempfile.TemporaryDirectory(prefix="mellum-seed-") as temporary:
        seed = Path(temporary)
        shutil.copytree(profile, seed / "profile")
        if {p.name for p in (seed / "profile").iterdir()} - {"models.json", "settings.json"}:
            raise ValueError("contained profile must contain only model/settings inputs")
        if suite.root and (suite.root / "base").is_dir():
            shutil.copytree(suite.root / "base", seed / "suite/base")
        if suite.start:
            shutil.copytree(suite.start, seed / "suite/start")
        if options.get("specs"):
            raise ValueError("temporary contained runner does not accept spec variants")
        write_json(seed / "input.json", {"suite": suite_data(suite), "options": {
            **{k: v for k, v in options.items() if k in {"arm", "deadline", "stall", "single_prompt", "context_files"}},
            "extras": contained_extras(options.get("extras", ())),
            **({"run_name": run_name, "gate_config": {"task_id": task_id}} if protected else {})}})
        if protected:
            (seed / "gate").mkdir()
        with Container(image, control) as container:
            container.seed(seed)
            container.start_relay(inference_target)
            output_path = control / "execution-output.txt"
            host_started = time.monotonic()
            deadline_at = host_started + (options.get("deadline") or 600)
            gate = Gate(task_id, package, deadline_at) if protected else None
            host_timeout = False
            host_interrupted = False
            host_integrity_error = None
            with output_path.open("w") as output:
                try:
                    argv = container.exec_argv("uv", "run", "--no-project", "--python", "3.14.2", "python", "/opt/entry.py", "model")
                    if gate:
                        result = run_model_with_gate(container, argv, gate,
                            f"/attempt/runs/{run_name}/workspace", control, output)
                    else:
                        result = run_bounded_command(argv, stdout=output, stderr=subprocess.STDOUT,
                            timeout=options.get("deadline") or 600)
                except subprocess.TimeoutExpired:
                    host_timeout = True
                except KeyboardInterrupt:
                    host_interrupted = True
                except ValueError as error:
                    if gate is None:
                        raise
                    host_integrity_error = str(error)
                    write_json(control / "integrity-error.json", {"detail": str(error)})
            host_elapsed = time.monotonic() - host_started
            if not host_timeout and not host_interrupted and not host_integrity_error and result.returncode:
                raise RuntimeError(f"contained execution failed; inspect {output_path}")
            # Retaining evidence may consume cleanup time after an expired task;
            # it grants no extra acceptance or inference allowance.
            container.export("/attempt/runs", control / "export", deadline_at=deadline_at + 30)
        candidates = list((control / "export/runs").iterdir())
        if len(candidates) != 1 or not candidates[0].is_dir():
            raise RuntimeError("ambiguous contained attempt export")
        run = runs_dir / candidates[0].name
        shutil.move(candidates[0], run)
        # These are host-authored controls, not authority imported from the agent.
        (run / "owner.json").unlink(missing_ok=True)
        write_json(run / "containment.json", {"backend": "temporary-docker", "image": image,
                   "control": str(control), "container_removed": True})
        if host_timeout or host_interrupted or host_integrity_error:
            execution = {"elapsed_seconds":round(host_elapsed,3), "exit_code":124,
                         "termination_reason":("integrity_error" if host_integrity_error else
                                               "interrupted" if host_interrupted else "deadline"),
                         "cleanup_ok":False, "host_watchdog":True}
        else:
            execution = json.loads((run / "execution.json").read_text())
        execution["inner_cleanup_ok"] = execution.get("cleanup_ok")
        execution["cleanup_ok"] = True  # The whole model container was removed.
        write_json(run / "execution.json", execution)
        if gate:
            from harness import execution_outcome
            completion = execution_outcome(run)["completion"]
            if host_integrity_error:
                gate.status = "integrity_error"
            elif completion != "settled":
                gate.status = completion if completion in {"deadline", "stalled"} else "model_error"
            elif gate.status != "verified" and gate.status in {"pending", "repairing"}:
                gate.status = "integrity_error"
            final = check_snapshot(run / "workspace", package, image, control / "final-check", gate.remaining())
            decision = gate.apply(final, snapshot_digest(run / "workspace"), final=True)
            write_json(control / "gate-journal.json", gate.journal)
            write_json(run / "acceptance.json", decision)
            write_json(run / "acceptance-journal.json", gate.journal)
            execution["elapsed_seconds"] = round(time.monotonic() - host_started, 3)
            write_json(run / "execution.json", execution)
        elif audit_package:
            final = check_snapshot(run / "workspace", audit_package, image, control / "final-check",
                                   max(0, deadline_at - time.monotonic()))
            write_json(run / "acceptance.json", {"status": "control", "result": final})
            execution["elapsed_seconds"] = round(time.monotonic() - host_started, 3)
            write_json(run / "execution.json", execution)
        if container.relay.returncode not in (0, -15):
            raise RuntimeError("relay failed; attempt requires review")
        return run


def grade_contained(run: Path, suite, image: str, versions: dict | None):
    from baseline import write_json
    control = run.parent / (".grading-" + uuid.uuid4().hex)
    with tempfile.TemporaryDirectory(prefix="mellum-grading-") as temporary:
        seed = Path(temporary)
        shutil.copytree(run / "workspace", seed / "grading/workspace")
        shutil.copytree(suite.tests, seed / "grader")
        write_json(seed / "input.json", {"suite": suite_data(suite, grading=True), "versions": versions})
        with Container(image, control) as container:
            container.seed(seed)
            container.execute("uv", "run", "--no-project", "--python", "3.14.2", "python", "/opt/entry.py", "grade",
                              stdout=(control / "stdout.txt").open("w"), stderr=subprocess.STDOUT)
            container.export("/attempt/grading", control / "export")
        exported = control / "export/grading"
        result = json.loads((exported / "result.json").read_text())
        for name in ("grade.json", "hidden-grade.json", "hidden-grade.started", "ruff.started", "complexipy.started", "pyrefly.started"):
            if (exported / name).is_file():
                shutil.copy2(exported / name, run / name)
        return result["grades"], result["scored"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "inspect", "qualify"])
    parser.add_argument("--image")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        print(build_image())
    elif args.command == "inspect":
        print(json.dumps(image_info(args.image), indent=2))
    else:
        from containment_qualification import qualify
        print(json.dumps(qualify(args.image, args.output), indent=2))


if __name__ == "__main__":
    main()
