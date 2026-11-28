"""Supervised training for the 1.5B distill: LoRA on every layer plus the nine new tool-token rows only.

The embedding table and the language-model head are wrapped (r1d/rows.py) so only the rows of the tokens
r1d/add_tokens.py added can move; every other row is frozen. Loss is cross-entropy on the completion only, and
the head runs only on completion positions (a 20K-token example would otherwise need a 12 GB logits table).

At each evaluation it reports the validation loss and the marker hit rate: of the positions where the next token
is `<｜tool▁calls▁begin｜>` (a call starting), how often the model ranks it first. Step 0 is the before.

    uv run --with mlx-lm==0.32.2 --with tokenizers python r1d/train_sft.py \
        --model ~/models/r1d-1.5b/hf-tooltokens --data r1d/data_sft_v1 --out r1d/adapters_sft_v1
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
START, N_NEW, MARKER = 151665, 11, 151665  # 9 tool markers + 2 thinking-switch tokens; MARKER = <｜tool▁calls▁begin｜>
LORA_KEYS = ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
             "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"]


def completion_loss(model, ids, n_prompt):
    """Mean cross-entropy over the completion tokens of one example (ids = prompt + completion)."""
    h = model.model(ids[None, :-1])[0, n_prompt - 1:]
    return nn.losses.cross_entropy(model.lm_head(h), ids[n_prompt:]).mean()


def marker_hits(logits, targets, marker=MARKER):
    """(positions where the model ranks `marker` first, positions whose target is `marker`)."""
    at = targets == marker
    return int((at & (logits.argmax(-1) == marker)).sum().item()), int(at.sum().item())


def main():
    from mlx.utils import tree_flatten
    import mlx.optimizers as optim
    from mlx_lm import load
    from mlx_lm.tuner.trainer import grad_checkpoint
    from mlx_lm.tuner.utils import linear_to_lora_layers
    from tokenizers import Tokenizer
    from pairs_io import read_pairs
    from rows import RowDeltaEmbedding, RowDeltaHead

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--examples", type=int, default=0, help="train on this many (0 = all), sampled with seed 0")
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--eval-every", type=int, default=50, help="in updates")
    ap.add_argument("--eval-n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--new-rows", type=int, default=N_NEW, help="trainable new-token rows from id 151665 (0: none, e.g. Mellum)")
    ap.add_argument("--lora-layers", type=int, default=0, help="LoRA on the last N layers (0: all)")
    ap.add_argument("--lora-keys", choices=["all-linear", "default"], default="all-linear",
                    help="all-linear: attention and MLP projections (dense models); default: mlx-lm's choice (MoE models)")
    ap.add_argument("--marker", default="<｜tool▁calls▁begin｜>", help="the token that starts a tool call, for the hit rate")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"{out} exists: train into a new folder")
    out.mkdir(parents=True)
    random.seed(a.seed); mx.random.seed(a.seed)

    model_dir = Path(a.model).expanduser()
    model, _ = load(str(model_dir))
    tok = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    model.freeze()
    lora = {"rank": a.rank, "scale": a.scale, "dropout": 0.0}
    if a.lora_keys == "all-linear":
        lora["keys"] = LORA_KEYS
    n_layers = a.lora_layers or len(model.model.layers)
    linear_to_lora_layers(model, n_layers, lora)
    if a.new_rows:
        model.model.embed_tokens = RowDeltaEmbedding(model.model.embed_tokens, START, a.new_rows)
        model.lm_head = RowDeltaHead(model.lm_head, START, a.new_rows)
    marker = tok.token_to_id(a.marker)
    assert marker is not None, f"{a.marker} is not a single token in this tokenizer"
    grad_checkpoint(model.model.layers[0])
    n_train = sum(v.size for _, v in tree_flatten(model.trainable_parameters()))
    print(f"trainable parameters: {n_train:,}", flush=True)

    def encode(row):
        p = tok.encode(row["prompt"], add_special_tokens=False).ids
        c = tok.encode(row["completion"], add_special_tokens=False).ids
        return mx.array(p + c), len(p)

    train, valid = read_pairs(a.data, "train"), read_pairs(a.data, "valid")
    random.shuffle(train)
    if a.examples:
        train = train[:a.examples]
    valid = random.Random(1).sample(valid, min(a.eval_n, len(valid)))
    # the marker check needs examples that start a call
    print(f"train {len(train)} examples, {sum(r['tokens'] for r in train):,} tokens; eval {len(valid)}", flush=True)

    def evaluate(step):
        losses, hit, total = [], 0, 0
        for row in valid:
            ids, n_p = encode(row)
            h = model.model(ids[None, :-1])[0, n_p - 1:]
            logits = model.lm_head(h)
            targets = ids[n_p:]
            losses.append(nn.losses.cross_entropy(logits, targets).mean().item())
            h1, t1 = marker_hits(logits, targets, marker)
            hit, total = hit + h1, total + t1
        rec = {"update": step, "val_loss": round(sum(losses) / len(losses), 5),
               "marker_hits": hit, "marker_positions": total, "marker_rate": round(hit / max(total, 1), 4)}
        print("[eval]", json.dumps(rec), flush=True)
        return rec

    opt = optim.AdamW(learning_rate=a.lr, weight_decay=0.0)
    loss_and_grad = nn.value_and_grad(model, completion_loss)
    log = {"settings": vars(a), "trainable_parameters": n_train, "train": [], "eval": [evaluate(0)]}

    def save(name):
        mx.save_safetensors(str(out / name), dict(tree_flatten(model.trainable_parameters())))

    acc_grads, acc_loss, step, t0 = None, 0.0, 0, time.time()
    n_updates = len(train) // a.accum
    for i, row in enumerate(train):
        ids, n_p = encode(row)
        loss, grads = loss_and_grad(model, ids, n_p)
        acc_grads = grads if acc_grads is None else nn.utils.tree_map(lambda x, y: x + y, acc_grads, grads)
        acc_loss += loss.item()
        if (i + 1) % a.accum:
            continue
        opt.update(model, nn.utils.tree_map(lambda g: g / a.accum, acc_grads))
        mx.eval(model.parameters(), opt.state)
        step += 1
        mins = (time.time() - t0) / 60
        print(f"[train] update {step}/{n_updates}: loss {acc_loss / a.accum:.4f} | {mins:.1f} min, "
              f"~{mins / step * (n_updates - step):.0f} min left, peak {mx.get_peak_memory() / 1e9:.1f} GB", flush=True)
        log["train"].append({"update": step, "loss": round(acc_loss / a.accum, 5)})
        acc_grads, acc_loss = None, 0.0
        if step % a.eval_every == 0 or step == n_updates:
            log["eval"].append(evaluate(step))
            save(f"{step:04d}_adapters.safetensors")
            (out / "log.json").write_text(json.dumps(log, indent=1))
    save("adapters.safetensors")
    (out / "adapter_config.json").write_text(json.dumps({
        "fine_tune_type": "lora", "num_layers": n_layers, "lora_parameters": lora,
        "new_rows": {"start": START, "n": a.new_rows}}, indent=1))
    (out / "log.json").write_text(json.dumps(log, indent=1))
    print("=== TRAINING DONE", flush=True)


if __name__ == "__main__":
    main()
