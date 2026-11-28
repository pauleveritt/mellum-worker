"""Give DeepSeek-R1-Distill-Qwen-1.5B DeepSeek's tool-call markers as real tokens.

The distill's chat template already writes `<｜tool▁calls▁begin｜>` and friends, but its tokenizer has no such
tokens: each marker is split into several pieces, and the model was never taught to emit them. Its embedding
matrices have 271 spare rows (ids 151665-151935), so the markers become special tokens in those rows with no
resize. Each new row (input embedding and output head, which are not tied) starts as the mean of the rows of the
pieces the marker used to split into; every existing row is left exactly as it was.

    uv run --with mlx --with tokenizers --with numpy python r1d/add_tokens.py SRC_HF_DIR OUT_DIR
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

TOOL_TOKENS = ["<｜tool▁calls▁begin｜>", "<｜tool▁calls▁end｜>", "<｜tool▁call▁begin｜>", "<｜tool▁call▁end｜>",
               "<｜tool▁sep｜>", "<｜tool▁outputs▁begin｜>", "<｜tool▁outputs▁end｜>", "<｜tool▁output▁begin｜>",
               "<｜tool▁output▁end｜>"]
START = 151665
TEMPLATE = Path(__file__).parent / "deepseek_tools.jinja"


def add_to_tokenizer(tok_json, cfg, tokens, start):
    """(tokenizer.json, tokenizer_config.json) with `tokens` added as special tokens from id `start`."""
    tok_json, cfg = json.loads(json.dumps(tok_json)), json.loads(json.dumps(cfg))
    taken = {t["id"] for t in tok_json["added_tokens"]} | set(tok_json["model"]["vocab"].values())
    # transformers' Qwen2 tokenizer rebuilds its special tokens from added_tokens_decoder whenever that section
    # exists, so it must list every added token, the old ones too, or they are laid out again at new ids
    decoder = cfg.setdefault("added_tokens_decoder", {})
    for t in tok_json["added_tokens"]:
        decoder.setdefault(str(t["id"]), {k: v for k, v in t.items() if k != "id"})
    for i, content in enumerate(tokens):
        tid = start + i
        assert tid not in taken, f"id {tid} is already used"
        entry = {"content": content, "single_word": False, "lstrip": False, "rstrip": False,
                 "normalized": False, "special": True}
        tok_json["added_tokens"].append({"id": tid, **entry})
        cfg.setdefault("added_tokens_decoder", {})[str(tid)] = entry
    return tok_json, cfg


def init_rows(weight, pieces):
    """`weight` with each new row {id: piece ids} set to the mean of its pieces' rows; other rows untouched."""
    out = weight.copy()
    for tid, ids in pieces.items():
        out[tid] = weight[ids].mean(0)
    return out


def main(src, out):
    import mlx.core as mx
    from tokenizers import Tokenizer

    src, out = Path(src), Path(out)
    if out.exists():
        raise SystemExit(f"{out} exists: build into a new folder")
    tok_json = json.loads((src / "tokenizer.json").read_text())
    cfg = json.loads((src / "tokenizer_config.json").read_text())
    old = Tokenizer.from_str(json.dumps(tok_json))
    pieces = {START + i: old.encode(t, add_special_tokens=False).ids for i, t in enumerate(TOOL_TOKENS)}
    new_json, new_cfg = add_to_tokenizer(tok_json, cfg, TOOL_TOKENS, START)
    if TEMPLATE.is_file():
        new_cfg["chat_template"] = TEMPLATE.read_text()
    shutil.copytree(src, out, ignore=shutil.ignore_patterns(".cache", "*.safetensors", "figures"))
    (out / "tokenizer.json").write_text(json.dumps(new_json, ensure_ascii=False, indent=2))
    (out / "tokenizer_config.json").write_text(json.dumps(new_cfg, ensure_ascii=False, indent=2))
    report = {"tokens": {t: {"id": START + i, "was": pieces[START + i]} for i, t in enumerate(TOOL_TOKENS)}}
    for f in sorted(src.glob("*.safetensors")):
        w = mx.load(str(f))
        for name in ("model.embed_tokens.weight", "lm_head.weight"):
            if name in w:
                dtype = w[name].dtype
                rows = init_rows(np.array(w[name].astype(mx.float32)), pieces)
                w[name] = mx.array(rows).astype(dtype)
                report[name] = list(w[name].shape)
        mx.save_safetensors(str(out / f.name), w, metadata={"format": "pt"})
    (out / "ADDED_TOKENS.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:3])
