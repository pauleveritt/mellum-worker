"""Fold a train_sft.py adapter (LoRA plus new-row deltas) into plain Hugging Face weights.

The result is an ordinary model folder: the token-surgery tokenizer and template, with weights that need no
adapter, ready for convert_hf_to_gguf.py.

    uv run --with mlx-lm==0.32.2 python r1d/fuse.py BASE_HF_DIR ADAPTER_DIR OUT_DIR [--checkpoint 0350]
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np


def fuse_weights(weights, adapters, scale, start):
    """New {name: array} with every LoRA pair and row delta in `adapters` folded into `weights` (float32)."""
    out = dict(weights)
    for key in adapters:
        if key.endswith(".lora_a"):
            name = key[:-len(".lora_a")]
            a, b = adapters[key].astype(np.float32), adapters[name + ".lora_b"].astype(np.float32)
            w = weights[name + ".weight"].astype(np.float32)  # KeyError when the base has no such weight
            out[name + ".weight"] = w + scale * (a @ b).T  # LoRALinear: y = x W^T + scale (x a) b
        elif key.endswith(".delta"):
            name = key[:-len(".delta")] + ".weight"
            w = weights[name].astype(np.float32).copy()
            d = adapters[key].astype(np.float32)
            w[start:start + len(d)] += d
            out[name] = w
    return out


def main():
    import mlx.core as mx

    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("adapter"); ap.add_argument("out")
    ap.add_argument("--checkpoint", default="", help="e.g. 0350 for 0350_adapters.safetensors (default: final)")
    a = ap.parse_args()
    base, adapter, out = Path(a.base).expanduser(), Path(a.adapter), Path(a.out).expanduser()
    if out.exists():
        raise SystemExit(f"{out} exists: fuse into a new folder")
    cfg = json.loads((adapter / "adapter_config.json").read_text())
    name = f"{a.checkpoint}_adapters.safetensors" if a.checkpoint else "adapters.safetensors"
    adapters = {k: np.array(v.astype(mx.float32)) for k, v in mx.load(str(adapter / name)).items()}
    shutil.copytree(base, out, ignore=shutil.ignore_patterns("*.safetensors", ".cache"))
    used = set()
    for f in sorted(base.glob("*.safetensors")):
        raw = mx.load(str(f))
        dtypes = {k: v.dtype for k, v in raw.items()}
        weights = {k: np.array(v.astype(mx.float32)) for k, v in raw.items()}
        mine = {k: v for k, v in adapters.items()
                if (k.rsplit(".", 1)[0] + ".weight") in weights}
        used |= set(mine)
        fused = fuse_weights(weights, mine, cfg["lora_parameters"]["scale"], cfg["new_rows"]["start"])
        mx.save_safetensors(str(out / f.name), {k: mx.array(v).astype(dtypes[k]) for k, v in fused.items()},
                            metadata={"format": "pt"})
    missing = set(adapters) - used
    assert not missing, f"adapter tensors with no base weight: {sorted(missing)[:5]}"
    (out / "FUSED_FROM.json").write_text(json.dumps({"base": str(base), "adapter": str(adapter.resolve()),
                                                     "file": name, "config": cfg}, indent=1))
    print(f"fused {len(adapters)} adapter tensors into {out}")


if __name__ == "__main__":
    main()
