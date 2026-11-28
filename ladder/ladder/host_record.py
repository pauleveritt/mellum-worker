"""What a run measured on, read from the live host rather than typed in.

A baseline anyone can replicate has to name its server build, the model it
served and the GPU it ran on. oMLX runs record theirs through the admin API;
these cover every other OpenAI-compatible server (vLLM, llama.cpp, mlx_lm).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from urllib.parse import urlsplit

MODEL_KEYS = ("id", "root", "max_model_len")


def _get_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def server_identity(base_url: str, timeout: float = 5) -> dict:
    """The server's version (vLLM's ``/version``; ``None`` where there is none) and served models."""
    parts = urlsplit(base_url)
    origin = f"{parts.scheme}://{parts.netloc}"
    try:
        models = [
            {k: entry[k] for k in MODEL_KEYS if k in entry}
            for entry in _get_json(f"{base_url.rstrip('/')}/models", timeout).get("data", [])
        ]
    except (OSError, ValueError) as error:
        return {"version": None, "models": None, "error": str(error)}
    try:
        version = _get_json(f"{origin}/version", timeout).get("version")
    except (OSError, ValueError):
        version = None
    return {"version": version, "models": models}


def gpu_identity(env: dict | None = None) -> list[dict] | None:
    """Every GPU's name, memory and driver from ``nvidia-smi``; ``None`` on a host without one."""
    path = env.get("PATH") if env is not None else None
    binary = shutil.which("nvidia-smi", path=path)
    if not binary:
        return None
    try:
        result = subprocess.run(
            [binary, "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30, check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    gpus = []
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) == 3 and fields[1].isdigit():
            gpus.append({"name": fields[0], "memory_mib": int(fields[1]), "driver": fields[2]})
    return gpus or None
