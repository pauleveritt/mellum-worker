#!/usr/bin/env python3
"""Pin everything a trained model depends on, so it can be rebuilt bit for bit.

    run_manifest.py --name mix120 --data data_dpo_mix120 --base <6bit MLX dir> --adapter adapters_dpo_mix120 \\
        --log <trainer log> --settings '{"beta": 10, ...}' [--gguf <file>] --out models/mix120/MANIFEST.json

The manifest records the code commit (and whether the tree was dirty), the training data's checksums and row
counts, the base model's weight checksums and quantisation, the adapter's checksums, the exact settings, every
logged update and held-out eval, the package versions, and (when given) the final GGUF's checksum.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

PACKAGES = ("mlx", "mlx-lm", "mlx-lm-lora", "numpy", "safetensors", "torch", "transformers")
TRAIN = re.compile(r"\[train\] ep \d+ update (\d+)/\d+: loss ([-\d.e]+) acc ([-\d.e]+) margin ([-\d.e]+)")
EVAL = re.compile(r"\[eval\] update (\d+): val loss ([-\d.e]+) acc ([-\d.e]+) margin ([-\d.e]+)")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_train_log(text):
    row = lambda m: {"update": int(m[0]), "loss": float(m[1]), "acc": float(m[2]), "margin": float(m[3])}  # noqa: E731
    return {"train": [row(m) for m in TRAIN.findall(text)], "eval": [row(m) for m in EVAL.findall(text)]}


def _git(repo, *args):
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else None


def _versions():
    out = {"python": platform.python_version()}
    for name in PACKAGES:
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = None
    return out


def build_manifest(name, data_dir, base_dir, adapter_dir, settings, train_log, repo, gguf=None, extra=None):
    data_dir, base_dir, adapter_dir = Path(data_dir), Path(base_dir), Path(adapter_dir)
    config = json.loads((base_dir / "config.json").read_text()) if (base_dir / "config.json").is_file() else {}
    quant = config.get("quantization") or {}
    manifest = {
        "name": name,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "machine": f"{platform.system()} {platform.machine()} {platform.node()}",
        "git": {"commit": _git(repo, "rev-parse", "HEAD"),
                "dirty": bool(_git(repo, "status", "--porcelain", "--", "learn/finetune"))},
        "data": {"dir": str(data_dir), "source_md": (data_dir / "SOURCE.md").is_file(),
                 "files": {p.name: {"sha256": sha256(p), "rows": sum(1 for _ in open(p))}
                           for p in sorted(data_dir.glob("*.jsonl"))}},
        "base": {"dir": str(base_dir),
                 "quantization": {k: v for k, v in quant.items() if not k.startswith("model.")},
                 "files": {p.name: sha256(p) for p in sorted(base_dir.glob("*.safetensors"))}},
        "adapter": {"dir": str(adapter_dir),
                    "files": {p.name: sha256(p) for p in sorted(adapter_dir.glob("*"))
                              if p.is_file() and not p.name.startswith("resume")}},
        "settings": settings,
        "packages": _versions(),
        "log": parse_train_log(train_log),
    }
    if gguf:
        manifest["gguf"] = {"file": Path(gguf).name, "sha256": sha256(gguf), "bytes": Path(gguf).stat().st_size}
    if extra:
        manifest.update(extra)
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--settings", required=True, help="JSON of the trainer arguments")
    ap.add_argument("--gguf")
    ap.add_argument("--extra", default="{}", help="JSON merged in (e.g. llama.cpp commit, screen results)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    m = build_manifest(a.name, a.data, a.base, a.adapter, json.loads(a.settings), Path(a.log).read_text(),
                       repo, a.gguf, json.loads(a.extra))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(m, indent=2) + "\n")
    print(f"manifest: {a.out}")


if __name__ == "__main__":
    main()
