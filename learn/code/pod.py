#!/usr/bin/env python3
"""F.6's held pod: the setup commands, built from the pod pin card so no script can drift from it.

A rental is one Secure Cloud pod, one GPU, one session at a time. `scripts/pod/push.sh` copies the
checkout up and runs `scripts/pod/bootstrap.sh`, which installs uv and then this:

    uv run python learn/code/pod.py setup
    uv run python learn/code/pod.py serve

The tools, the checkout and live runs sit on the container disk: /workspace on a Secure Cloud pod is
NFS and refuses chown, so a session user cannot own a run tree there. Weights live on /workspace, and
`keep-results` copies finished runs there, because the container disk is cleared on stop.

Renting, stopping and terminating are not here: each rental is a person's yes in chat.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from pathlib import Path

import conformance

REPO = Path(__file__).resolve().parents[2]
SESSION_USER = "mellum-session"
GRADE_USER = "mellum-grade"
PORT = 8001
DEFAULTS = {"prefix": "/opt/mellum", "repo": "/opt/mellum/repo", "weights": "/workspace/mellum/models"}
q = shlex.quote


def cgroup_cpus(cpu_max: str, *, fallback: int) -> int:
    """The CPUs the pod's cgroup grants: `nproc` reports the whole host, which oversubscribes builds and threads."""
    quota, period = cpu_max.split()[:2]
    return fallback if quota == "max" else max(1, int(quota) // int(period))


def effective_cpus() -> int:
    try:
        return cgroup_cpus(Path("/sys/fs/cgroup/cpu.max").read_text(), fallback=os.cpu_count() or 1)
    except OSError:
        return os.cpu_count() or 1


def apt_commands(pins: dict) -> list[str]:
    return ["apt-get update", "apt-get install -y --no-install-recommends " + " ".join(map(q, pins["pod"]["apt"]))]


def user_commands() -> list[str]:
    return [command for user in (SESSION_USER, GRADE_USER) for command in (
        f"id -u {user} >/dev/null 2>&1 || useradd --create-home --shell /bin/bash {user}",
        f"passwd --lock {user}")]


def node_commands(pins: dict, *, prefix: str) -> list[str]:
    version, sha = pins["tooling"]["node"], pins["pod"]["node_sha256"]
    node = f"node-v{version}-linux-x64"
    tarball = f"{prefix}/{node}.tar.xz"
    return [f"curl -fsSL -o {q(tarball)} https://nodejs.org/dist/v{version}/{node}.tar.xz",
            f"echo {q(sha + '  ' + tarball)} | sha256sum --check",
            f"tar -xJf {q(tarball)} -C {q(prefix)}",
            *(f"ln -sf {q(f'{prefix}/{node}/bin/{tool}')} {q(f'{prefix}/bin/{tool}')}" for tool in ("node", "npm", "npx"))]


def python_commands(pins: dict, *, prefix: str) -> list[str]:
    return [f"{q(prefix + '/bin/uv')} python install {q(pins['pod']['python'])}"]


def pi_commands(pins: dict, *, prefix: str) -> list[str]:
    return [f"{q(prefix + '/bin/npm')} install -g --prefix {q(prefix)} {q(pins['pod']['pi_package'])}",
            f"{q(prefix + '/bin/pi')} --version"]


def build_commands(pins: dict, *, prefix: str, jobs: int) -> list[str]:
    """Full history: llama.cpp derives its build number from it, so a shallow clone misreports the build."""
    pod = pins["pod"]
    number, commit = pins["build"]["build_info"].removeprefix("b").split("-")
    source = f"{prefix}/llama.cpp"
    return [f"rm -rf {q(source)}",
            f"git clone --no-checkout {q(pod['llama_repo'])} {q(source)}",
            f"git -C {q(source)} checkout --detach {pod['llama_commit']}",
            f"cmake -S {q(source)} -B {q(source + '/build')} -DGGML_CUDA=ON -DGGML_NATIVE=OFF "
            f"-DCMAKE_CUDA_ARCHITECTURES={q(pod['cuda_architectures'])} -DCMAKE_BUILD_TYPE=Release",
            f"cmake --build {q(source + '/build')} --target llama-server llama-perplexity -j {jobs}",
            *(f"ln -sf {q(f'{source}/build/bin/{tool}')} {q(f'{prefix}/bin/{tool}')}"
              for tool in ("llama-server", "llama-perplexity")),
            f"{q(prefix + '/bin/llama-server')} --version 2>&1 | grep -F {q(f'build {number}, commit {commit}')}"]


def weights_commands(pins: dict, *, dest: str) -> list[str]:
    pod, weights = pins["pod"], pins["weights"]
    path = f"{dest}/{weights['file']}"
    return [f"mkdir -p {q(dest)}",
            f"curl -fL --retry 3 -o {q(path)} https://huggingface.co/{pod['weights_repo']}/resolve/"
            f"{pod['weights_revision']}/{weights['file']}",
            f"echo {q(weights['sha256'] + '  ' + path)} | sha256sum --check"]


def lock_commands(*, prefix: str, repo: str) -> list[str]:
    """The tools stay readable; the checkout, which holds the hidden grader, becomes root's alone."""
    return [f"chmod -R a+rX {prefix}", f"chown -R root:root {repo}", f"chmod -R go-rwx {repo}"]


def warm_commands(pins: dict, *, prefix: str, repo: str) -> list[str]:
    """The session user's uv cache, so the mediated test's `uv run --offline` has what it needs."""
    base = f"{repo}/{pins['pod']['dependency_project']}"
    home = f"/home/{SESSION_USER}"
    warm = f"{home}/warm"
    env = (f"HOME={home} USER={SESSION_USER} PATH={prefix}/bin:/usr/local/bin:/usr/bin:/bin "
           f"UV_PYTHON_INSTALL_DIR={prefix}/python UV_PYTHON_DOWNLOADS=never UV_CACHE_DIR={home}/.cache/uv")
    session = f"runuser -u {SESSION_USER} -- env {env} bash -ec"
    return [f"rm -rf {warm}", f"cp -r {base} {warm}", f"chown -R {SESSION_USER}: {warm}",
            f"{session} {q(f'cd {warm} && uv sync --frozen && uv run --offline python -m pytest --version')}",
            f"rm -rf {warm}"]


def free_ports_commands() -> list[str]:
    """The image's web server holds 8000 and 8001: the port guard and the model server's port."""
    return ["nginx -s stop 2>/dev/null || pkill -x nginx || true", "sleep 1",
            f"! lsof -nP -iTCP:{PORT} -sTCP:LISTEN", "! lsof -nP -iTCP:8000 -sTCP:LISTEN"]


def keep_results_command(*, runs: str, results: str) -> str:
    """Copy runs to the volume: -rlt, not -a, since the volume refuses chown; a session's venv is not evidence."""
    return (f"mkdir -p {q(results)} && rsync -rlt --exclude .venv --exclude __pycache__ --exclude node_modules "
            f"{q(runs + '/')} {q(results + '/')}")


def serve_commands(pins: dict, *, prefix: str, weights: str, threads: int, log: str) -> list[str]:
    model = f"{weights}/{pins['weights']['file']}"
    argv = conformance.server_argv(pins, binary=f"{prefix}/bin/llama-server", model=model, port=PORT,
                                   threads=threads, log=log)
    return [*free_ports_commands(), "tmux kill-session -t mellum-llama 2>/dev/null || true",
            f"tmux new-session -d -s mellum-llama {q(shlex.join(argv))}"]


def run_steps(steps: list[tuple[str, list[str]]], done: Path) -> None:
    """Run each step's commands with bash -e, in order; a finished step is marked and never repeated."""
    done.mkdir(parents=True, exist_ok=True)
    for name, commands in steps:
        if (done / name).exists():
            print(f"[pod] {name}: already done", flush=True)
            continue
        print(f"[pod] {name}", flush=True)
        if subprocess.run(["bash", "-ec", "\n".join(commands)], check=False).returncode != 0:
            raise SystemExit(f"pod setup failed at step {name}")
        (done / name).touch()


def setup_steps(pins: dict, *, prefix: str, repo: str, weights: str, jobs: int) -> list[tuple[str, list[str]]]:
    path = (f"export PATH={prefix}/bin:/usr/local/cuda/bin:$PATH UV_PYTHON_INSTALL_DIR={prefix}/python "
            f"UV_PYTHON_BIN_DIR={prefix}/bin")
    return [(name, [path, *commands]) for name, commands in (
        ("apt", apt_commands(pins)),
        ("users", user_commands()),
        ("node", node_commands(pins, prefix=prefix)),
        ("python", python_commands(pins, prefix=prefix)),
        ("pi", pi_commands(pins, prefix=prefix)),
        ("llama", build_commands(pins, prefix=prefix, jobs=jobs)),
        ("weights", weights_commands(pins, dest=weights)),
        ("lock", lock_commands(prefix=prefix, repo=repo)),
        ("warm", warm_commands(pins, prefix=prefix, repo=repo)),
    )]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("setup", "serve", "cpus", "keep-results"))
    parser.add_argument("--prefix", default=DEFAULTS["prefix"])
    parser.add_argument("--repo", default=DEFAULTS["repo"])
    parser.add_argument("--weights", default=DEFAULTS["weights"])
    parser.add_argument("--log", default="/tmp/llama-server.log")
    parser.add_argument("--runs", help="keep-results: the batch's directory on the container disk")
    parser.add_argument("--results", help="keep-results: where on the volume to copy it")
    args = parser.parse_args(argv)
    pins = conformance.load_pins(conformance.POD_PINS)
    cpus = effective_cpus()
    if args.command == "cpus":
        print(cpus)
    elif args.command == "setup":
        run_steps(setup_steps(pins, prefix=args.prefix, repo=args.repo, weights=args.weights, jobs=cpus),
                  Path(args.prefix) / "done")
    elif args.command == "keep-results":
        return subprocess.run(["bash", "-ec", keep_results_command(runs=args.runs, results=args.results)],
                              check=False).returncode
    else:
        run_steps([("serve", serve_commands(pins, prefix=args.prefix, weights=args.weights, threads=cpus,
                                            log=args.log))],
                  Path("/tmp/mellum-serve-" + str(os.getpid())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
