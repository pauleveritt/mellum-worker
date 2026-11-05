"""The portable rig's pin card: what every host serves, bootstraps and limits.

`scripts/rig/pins.json` is the single source. Changing any value makes a new
rig, not a replicate (docs/superpowers/specs/2026-11-05-portable-floor-design.md).
"""
import hashlib
import json
import os
import pwd
import re
import shlex
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PINS = REPO / "scripts/rig/pins.json"

REQUIRED = {
    "weights": ("repo", "revision", "file", "sha256", "alias"),
    "build": ("repo", "tag", "commit", "build_info", "cuda_architectures"),
    "server": ("host", "context", "parallel", "slot_context", "kv_unified", "jinja", "flash_attention",
               "continuous_batching", "batch", "microbatch", "cache_type_k", "cache_type_v",
               "gpu_layers", "log_verbosity"),
    "client": ("temperature", "top_p", "top_k", "max_tokens"),
    "bootstrap": ("node", "uv", "python", "pi", "dependency_project", "checkers", "apt"),
    "acceptance_package_sha256": (),
    "session": ("max_requests", "max_output_tokens", "max_tokens_per_request", "unknown_usage_charge",
                "open_tool_seconds", "wall_safety_seconds"),
    "allowlist": ("min_compute_capability", "gpu_count", "min_driver_major", "platform"),
}


def load_pins(path: Path = PINS) -> dict:
    pins = json.loads(Path(path).read_text())
    for section, keys in REQUIRED.items():
        if section not in pins:
            raise ValueError(f"pin card is missing {section}")
        for key in keys:
            if key not in pins[section]:
                raise ValueError(f"pin card is missing {section}.{key}")
    if pins["server"]["flash_attention"] != "on":
        raise ValueError("pin card must set server.flash_attention to on; auto may resolve differently per GPU")
    return pins


def pins_digest(pins: dict) -> str:
    return hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def server_argv(pins: dict, *, binary: str, model: str, port: int, threads: int, log: str) -> list[str]:
    """The frozen LC.34–LC.38 server command, with flash attention pinned on."""
    s = pins["server"]
    argv = [binary, "-m", model, "-a", pins["weights"]["alias"], "--host", s["host"], "--port", str(port),
            "-c", str(s["context"]), "-np", str(s["parallel"])]
    if not s["kv_unified"]:
        argv.append("--no-kv-unified")
    if s["jinja"]:
        argv.append("--jinja")
    argv += ["-fa", s["flash_attention"]]
    if s["continuous_batching"]:
        argv.append("--cont-batching")
    argv += ["-t", str(threads), "-tb", str(threads), "-b", str(s["batch"]), "-ub", str(s["microbatch"]),
             "-ctk", s["cache_type_k"], "-ctv", s["cache_type_v"], "-ngl", str(s["gpu_layers"]),
             "-lv", str(s["log_verbosity"]), "--log-file", log]
    return argv


# Host commands. Every string is built from the pin card, so no shell script can
# drift from it. They run on a fresh Linux pod as root, over SSH, in order.

def checkout_commands(repo_url: str, commit: str, dest: str) -> list[str]:
    q = shlex.quote
    return [f"git clone --no-checkout {q(repo_url)} {q(dest)}",
            f"git -C {q(dest)} checkout --detach {q(commit)}",
            f'test "$(git -C {q(dest)} rev-parse HEAD)" = {q(commit)}']


def bootstrap_commands(pins: dict, *, prefix: str, repo: str, platform: str | None = None) -> list[str]:
    """Install the pinned tools. A pod is the allowlist platform; the Mac is darwin-arm64 (no apt, no rig users)."""
    q = shlex.quote
    boot = pins["bootstrap"]
    platform = platform or pins["allowlist"]["platform"]
    linux = platform.startswith("linux")
    sha256_check = "sha256sum --check" if linux else "shasum -a 256 --check"
    node = f"node-v{boot['node']['version']}-{platform}"
    tarball = f"{prefix}/{node}.tar.xz"
    bin_dir = f"{prefix}/bin"
    uv = f"{bin_dir}/uv"
    project = f"{repo}/{boot['dependency_project']}"
    python_dir, grade_cache, dependencies = f"{prefix}/python", f"{prefix}/cache-grade", f"{prefix}/dependencies"
    commands = [
        *(["apt-get update && apt-get install -y --no-install-recommends " + " ".join(map(q, boot["apt"]))]
          if linux else []),
        f"mkdir -p {q(bin_dir)}",
        f"curl -fsSL -o {q(tarball)} https://nodejs.org/dist/v{boot['node']['version']}/{node}.tar.xz",
        f"echo {q(boot['node']['sha256'][platform] + '  ' + tarball)} | {sha256_check}",
        f"tar -xJf {q(tarball)} -C {q(prefix)}",
        *(f"ln -sf {q(f'{prefix}/{node}/bin/{tool}')} {q(f'{bin_dir}/{tool}')}" for tool in ("node", "npm", "npx")),
        f"curl -LsSf https://astral.sh/uv/{boot['uv']}/install.sh | env UV_INSTALL_DIR={q(bin_dir)} UV_NO_MODIFY_PATH=1 sh",
        f"UV_PYTHON_INSTALL_DIR={q(python_dir)} UV_PYTHON_BIN_DIR={q(bin_dir)} {q(uv)} python install {boot['python']}",
        f"PATH={q(bin_dir)}:$PATH {q(bin_dir + '/npm')} install -g --prefix {q(prefix)} {q(boot['pi'])}",
        # A copy under the prefix: syncing inside the suite fixture would put a .venv in every workspace.
        f"mkdir -p {q(dependencies)}",
        f"cp {q(project + '/pyproject.toml')} {q(project + '/uv.lock')} {q(dependencies + '/')}",
        f"UV_CACHE_DIR={q(grade_cache)} UV_PYTHON_INSTALL_DIR={q(python_dir)} {q(uv)} sync --frozen "
        f"--project {q(dependencies)} --python {boot['python']}",
        *(f"UV_CACHE_DIR={q(grade_cache)} UV_PYTHON_INSTALL_DIR={q(python_dir)} "
          f"{q(bin_dir + '/uvx')} {q(f'{name}@{version}')} --version"
          for name, version in boot["checkers"].items()),
        f"chmod -R a+rX {q(prefix)}",
        # Grading runs `uv run --offline` as mellum-grade; the session user may read, never write, its cache.
        *([f"chown -R {GRADE_USER} {q(grade_cache)}"] if linux else []),
    ]
    return commands


def build_commands(pins: dict, *, prefix: str) -> list[str]:
    q = shlex.quote
    build = pins["build"]
    source = f"{prefix}/llama.cpp-{build['tag']}"
    return [
        f"git clone --no-checkout {q(build['repo'])} {q(source)}",
        f"git -C {q(source)} checkout --detach {q(build['commit'])}",
        f"cmake -S {q(source)} -B {q(source + '/build')} -DGGML_CUDA=ON -DGGML_NATIVE=OFF "
        f"-DCMAKE_CUDA_ARCHITECTURES={q(build['cuda_architectures'])} -DCMAKE_BUILD_TYPE=Release",
        f"cmake --build {q(source + '/build')} --target llama-server llama-perplexity -j",
        *(f"ln -sf {q(f'{source}/build/bin/{tool}')} {q(f'{prefix}/bin/{tool}')}"
          for tool in ("llama-server", "llama-perplexity")),
        f"{q(prefix + '/bin/llama-server')} --version 2>&1 | grep -F "
        f"{q('build ' + build['tag'].removeprefix('b') + ', commit ' + build['commit'][:9])}",
    ]


def fetch_weights_commands(pins: dict, *, dest: str) -> list[str]:
    q = shlex.quote
    w = pins["weights"]
    path = f"{dest}/{w['file']}"
    return [f"mkdir -p {q(dest)}",
            f"curl -fL --retry 3 -o {q(path)} https://huggingface.co/{w['repo']}/resolve/{w['revision']}/{w['file']}",
            f"echo {q(w['sha256'] + '  ' + path)} | sha256sum --check"]


def serve_commands(pins: dict, *, binary: str, model: str, port: int, threads: int, log: str) -> list[str]:
    argv = server_argv(pins, binary=binary, model=model, port=port, threads=threads, log=log)
    return [f"tmux new-session -d -s mellum-rig {shlex.quote(shlex.join(argv))}"]


def stop_server_commands() -> list[str]:
    return ["tmux kill-session -t mellum-rig"]


SESSION_USER = "mellum-session"
GRADE_USER = "mellum-grade"


def lock_checkout_commands(dest: str) -> list[str]:
    """After the rig users exist: only root and the grading user may read the checkout (hidden tests live there)."""
    q = shlex.quote
    return [f"chown -R root:{GRADE_USER} {q(dest)}", f"chmod -R u=rwX,g=rX,o= {q(dest)}"]


def chown_tree(path: Path, user: str) -> None:
    """Give a tree to a rig user without ever following a symlink (lchown), so a planted link cannot redirect it."""
    account = pwd.getpwnam(user)
    for target in [Path(path), *Path(path).rglob("*")]:
        os.chown(target, account.pw_uid, account.pw_gid, follow_symlinks=False)


def drop_privileges(user: str) -> dict:
    """Popen keywords that run as user with only its primary group (no inherited supplementary groups)."""
    return {"user": user, "group": pwd.getpwnam(user).pw_gid, "extra_groups": []}


def user_commands() -> list[str]:
    commands = []
    for user in (SESSION_USER, GRADE_USER):
        commands += [f"id -u {user} >/dev/null 2>&1 || useradd --create-home --shell /bin/bash {user}",
                     f"passwd --lock {user}"]
    return commands


def probe_python(prefix: str) -> Path:
    """The frozen dependency project's interpreter, which runs the acceptance probe."""
    return Path(prefix) / "dependencies/.venv/bin/python"


def user_env(prefix: str, user: str, *, home: str) -> dict[str, str]:
    """The environment a rig user runs with: pinned tools first, uv pointed at the prefix."""
    return {"PATH": f"{prefix}/bin:/usr/local/bin:/usr/bin:/bin", "HOME": home, "USER": user, "LANG": "C.UTF-8",
            "UV_PYTHON_INSTALL_DIR": f"{prefix}/python", "UV_PYTHON_DOWNLOADS": "never",
            "UV_CACHE_DIR": f"{prefix}/cache-grade" if user == GRADE_USER else f"{home}/.cache/uv"}


VERSION = re.compile(r"\d+\.\d+\.\d+")


def tool_versions(prefix: str | None) -> dict[str, str | None]:
    """Read back the bootstrap's own tools (from PATH when prefix is None).

    Checkers run through `uvx name@version`, so their version is the pin."""
    probes = {"node": "node", "pi": "pi", "uv": "uv", "python": "python3.14"}
    versions = {}
    for name, binary in probes.items():
        path = Path(prefix) / "bin" / binary if prefix is not None else (shutil.which(binary) or binary)
        try:
            out = subprocess.run([str(path), "--version"], capture_output=True, text=True, timeout=30)
            match = VERSION.search(out.stdout + out.stderr) if out.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            match = None
        versions[name] = match.group() if match else None
    return versions
