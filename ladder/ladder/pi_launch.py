"""Verify the executable and fixture environment used by a ladder attempt."""

import json
import os
import shutil
import subprocess
from pathlib import Path


def resolve_pi(executable: str) -> dict:
    found = shutil.which(executable)
    if not found:
        raise RuntimeError(f"Pi executable not found: {executable}")
    path = str(Path(found).absolute())
    try:
        proc = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Pi version probe failed: {path}: {error}") from error
    version = proc.stdout.strip()
    if proc.returncode or not version:
        raise RuntimeError(f"Pi version probe failed: {path}: {proc.stderr.strip()}")
    return {"executable": path, "version": version}


def same_venv_python(reported: str, python: Path) -> bool:
    """Whether the interpreter reported sys.executable as the venv's own python.

    The venv's directory is compared with symlinks resolved (macOS reaches its
    temp dir through /var -> /private/var, and Python 3.15 reports the real
    path), but not the interpreter link itself, which points out of the venv.
    """
    reported_path = Path(reported)
    return (reported_path.name == python.name
            and reported_path.parent.resolve() == python.parent.resolve())


def workspace_preflight(
    ws: Path, fixture: str, parent_env: dict[str, str]
) -> tuple[dict[str, str], dict]:
    env = {key: value for key, value in parent_env.items() if key != "VIRTUAL_ENV"}
    node = shutil.which("node", path=env.get("PATH"))
    if not node:
        raise RuntimeError("workspace preflight: Node executable not found")
    try:
        proc = subprocess.run(
            [node, "--version"],
            cwd=ws,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode or not proc.stdout.strip():
            raise RuntimeError("workspace preflight: Node version probe failed")
        metadata = {
            "node": {
                "executable": str(Path(node).resolve()),
                "version": proc.stdout.strip(),
            },
            "python": None,
        }
        if (ws / "pyproject.toml").exists():
            venv = ws / ".venv"
            python = venv / "bin" / "python"
            env["VIRTUAL_ENV"] = str(venv)
            env["PATH"] = str(python.parent) + os.pathsep + env.get("PATH", "")
            imports = ["pytest"]
            if fixture.startswith("agentclinic"):
                imports += ["fastapi", "turbohtml", "httpx"]
            script = (
                "import importlib,json,sys; "
                + "; ".join(f"importlib.import_module({name!r})" for name in imports)
                + '; print(json.dumps({"executable":sys.executable}))'
            )
            proc = subprocess.run(
                [str(python), "-c", script],
                cwd=ws,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode:
                raise RuntimeError(
                    f"workspace preflight: fixture imports failed: {proc.stderr.strip()}"
                )
            identity = json.loads(proc.stdout)
            if not same_venv_python(identity["executable"], python):
                raise RuntimeError(
                    "workspace preflight: Python executable differs from fixture environment"
                )
            metadata["python"] = {**identity, "imports": imports}
        return env, metadata
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
        raise RuntimeError(f"workspace preflight failed: {error}") from error


def subagents_revision(agent_dir: Path) -> str | None:
    """Identify the existing Git-installed host without reading its credentials."""
    repo = agent_dir / "git/github.com/nicobailon/pi-subagents"
    if not repo.exists():
        return None
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None
