"""The portable rig's pin card: what every host serves, bootstraps and limits.

`scripts/rig/pins.json` is the single source. Changing any value makes a new
rig, not a replicate (docs/superpowers/specs/2026-11-05-portable-floor-design.md).
"""
import hashlib
import json
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
