#!/usr/bin/env python3
"""Native-format IPO-DPO trainer for Mellum (4-bit MoE) on long agent trajectories.

Why our own loop: upstream mlx_lm_lora (5.10.2) has three defects for this job -
  * train.py never passes loss_type to train_dpo, so --dpo-cpo-loss-type is ignored
    (sigmoid on summed log-probs runs instead, which is length-biased);
  * its long-context path backprops with mx.grad(fn)(model) over ALL parameters,
    which raises on quantized weights (QuantizedMatmul has no weight vjp);
  * reset_prompt_cache cannot rebuild a RotatingKVCache (Mellum's sliding layers).
We reuse upstream's verified pieces (dpo_loss, get_token_scores, the one-token-
overlap chunk iterator) and own the step, so the code that trains is the code the
--check-grad test exercises.

Per pair: exact chunked forward scores (policy and frozen reference) -> IPO loss on
per-token-mean scores -> dL/d(score sum) weights -> chunked backward over LoRA
parameters only. The backward treats the KV cache from earlier chunks as constant
(truncated through context); --check-grad measures how far that is from the exact
full-sequence gradient.
"""
import argparse, json, time, math, os
import numpy as np
import mlx.core as mx, mlx.nn as nn, mlx.optimizers as optim
from mlx.utils import tree_flatten, tree_map
from mlx_lm import load
from mlx_lm.tuner.utils import linear_to_lora_layers
from mlx_lm.models.cache import make_prompt_cache
from mlx_lm_lora.trainer.dpo_trainer import get_token_scores, dpo_loss
from mlx_lm_lora.trainer.long_context import iter_cached_sft_chunks

BASE = "mlx-community/Mellum2-12B-A2.5B-Thinking-4bit"

def load_pairs(path):
    return [json.loads(l) for l in open(path)]

def arr(ids, mask):
    return (mx.array(np.asarray(ids, np.int32)[None]), mx.array(np.asarray(mask, np.float32)[None]))

def ntok(m):
    return mx.maximum(m[:, 1:].sum(-1), 1)

def chunked_score(model, x, m, step):
    """Exact (up to kernel numerics) sum of masked next-token log-probs, no grad."""
    cache = make_prompt_cache(model); n = x.shape[1]; tot = mx.zeros((x.shape[0],))
    for s, e in iter_cached_sft_chunks(n, step):
        tot = tot + mx.stop_gradient(get_token_scores(model, x[:, s:e], m[:, s:e], cache=cache)).sum(-1)
        mx.eval(tot)
        if e >= n: break
    return tot

def ipo_loss(pc, pr, rc, rr, cm, rm, beta):
    return dpo_loss(policy_chosen_score=pc, policy_rejected_score=pr,
                    reference_chosen_score=rc, reference_rejected_score=rr,
                    chosen_masks=cm, rejected_masks=rm, beta=beta, delta=0.0, loss_type="ipo")

def pair_grad(policy, ref, c, cm, r, rm, beta, step):
    nc, nr = ntok(cm), ntok(rm)
    pc, pr = chunked_score(policy, c, cm, step) / nc, chunked_score(policy, r, rm, step) / nr
    rc, rr = chunked_score(ref, c, cm, step) / nc, chunked_score(ref, r, rm, step) / nr
    loss, reward, _, met = ipo_loss(pc, pr, rc, rr, cm, rm, beta)
    gc, gr = mx.grad(lambda a, b: ipo_loss(a, b, rc, rr, cm, rm, beta)[0], argnums=[0, 1])(pc, pr)
    wc, wr = gc / nc, gr / nr                      # dL/d(raw score sum)
    grads = None
    for x, m, w in ((c, cm, wc), (r, rm, wr)):
        cache = make_prompt_cache(policy); n = x.shape[1]
        for s, e in iter_cached_sft_chunks(n, step):
            xs, ms = x[:, s:e], m[:, s:e]
            def f(model_):
                return (get_token_scores(model_, xs, ms, cache=cache).sum(-1) * w).sum()
            _, g = nn.value_and_grad(policy, f)(policy)
            grads = g if grads is None else tree_map(lambda a, b: a + b, grads, g)
            mx.eval(grads, [cc.state for cc in cache])
            if e >= n: break
    mx.eval(loss, reward)
    return loss.item(), grads, {k: float(v) for k, v in met.items()}, reward.tolist()

def exact_grad(policy, ref, c, cm, r, rm, beta):
    nc, nr = ntok(cm), ntok(rm)
    rc = mx.stop_gradient(get_token_scores(ref, c, cm).sum(-1)) / nc
    rr = mx.stop_gradient(get_token_scores(ref, r, rm).sum(-1)) / nr
    def F(model_):
        a = get_token_scores(model_, c, cm).sum(-1) / nc
        b = get_token_scores(model_, r, rm).sum(-1) / nr
        return ipo_loss(a, b, rc, rr, cm, rm, beta)[0]
    l, g = nn.value_and_grad(policy, F)(policy)
    mx.eval(l, g)
    return l.item(), g

def flat(g):
    return np.concatenate([np.array(v.astype(mx.float32)).ravel() for _, v in tree_flatten(g)])

def build_policy(rank, scale, num_layers):
    model, tok = load(BASE)
    model.freeze()
    linear_to_lora_layers(model, num_layers, {"rank": rank, "dropout": 0.0, "scale": scale, "use_dora": False}, use_dora=False)
    n_tr = sum(v.size for _, v in tree_flatten(model.trainable_parameters()))
    print(f"trainable params: {n_tr/1e6:.2f}M", flush=True)
    return model, tok

def build_ref():
    ref, _ = load(BASE); ref.freeze(); ref.eval(); return ref

def evaluate(policy, ref, pairs, beta, step):
    L, A, M = [], [], []
    for p in pairs:
        c, cm = arr(p["chosen"], p["chosen_mask"]); r, rm = arr(p["rejected"], p["rejected_mask"])
        nc, nr = ntok(cm), ntok(rm)
        pc, pr = chunked_score(policy, c, cm, step) / nc, chunked_score(policy, r, rm, step) / nr
        rc, rr = chunked_score(ref, c, cm, step) / nc, chunked_score(ref, r, rm, step) / nr
        l, _, _, met = ipo_loss(pc, pr, rc, rr, cm, rm, beta)
        L.append(l.item()); A.append(float(met["accuracies"])); M.append(float(met["margins"]))
    return float(np.mean(L)), float(np.mean(A)), float(np.mean(M))

def save_adapters(policy, out, rank, scale, num_layers, tag="adapters"):
    os.makedirs(out, exist_ok=True)
    mx.save_safetensors(f"{out}/{tag}.safetensors", dict(tree_flatten(policy.trainable_parameters())))
    json.dump({"fine_tune_type": "lora", "num_layers": num_layers,
               "lora_parameters": {"rank": rank, "dropout": 0.0, "scale": scale}},
              open(f"{out}/adapter_config.json", "w"), indent=2)

def main():
    global BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", default=BASE, help="MLX base to train; must match the model the data was rendered for")
    ap.add_argument("--out", default="adapters_dpo_native")
    ap.add_argument("--rank", type=int, default=8); ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--num-layers", type=int, default=16)
    ap.add_argument("--beta", type=float, default=10.0)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--accum", type=int, default=4, help="pairs per optimizer update")
    ap.add_argument("--step", type=int, default=512, help="chunk size")
    ap.add_argument("--eval-every", type=int, default=6, help="updates between held-out evals")
    ap.add_argument("--check-grad", action="store_true", help="compare chunked vs exact gradient, no training")
    ap.add_argument("--crop", type=int, default=3000, help="--check-grad: crop pair to fit an exact full pass")
    a = ap.parse_args()
    BASE = a.model
    np.random.seed(0)
    train, valid = load_pairs(f"{a.data}/train.jsonl"), load_pairs(f"{a.data}/valid.jsonl")
    policy, _ = build_policy(a.rank, a.scale, a.num_layers); ref = build_ref()

    if a.check_grad:
        p = min(train, key=lambda q: len(q["chosen"]) + len(q["rejected"]))
        c, cm = arr(p["chosen"][:a.crop], p["chosen_mask"][:a.crop]); r, rm = arr(p["rejected"][:a.crop], p["rejected_mask"][:a.crop])
        # move off the B=0 init so every LoRA tensor has a gradient path
        rng = np.random.default_rng(0)
        policy.update(tree_map(lambda v: v + mx.array(rng.normal(0, 1e-3, v.shape).astype(np.float32)).astype(v.dtype),
                               policy.trainable_parameters()))
        le, ge = exact_grad(policy, ref, c, cm, r, rm, a.beta); fe = flat(ge)
        for st in (512, 256):
            lc, gch, _, _ = pair_grad(policy, ref, c, cm, r, rm, a.beta, st); fc = flat(gch)
            cos = float(fe @ fc / (np.linalg.norm(fe) * np.linalg.norm(fc) + 1e-12))
            print(f"[check-grad] crop {a.crop}: loss exact {le:.6f} chunked@{st} {lc:.6f} | "
                  f"grad cosine {cos:.4f} | norm ratio {np.linalg.norm(fc)/np.linalg.norm(fe):.3f}", flush=True)
        return

    opt = optim.Adam(learning_rate=a.lr)
    upd_per_epoch = math.ceil(len(train) / a.accum); total = upd_per_epoch * a.epochs
    print(f"train {len(train)} pairs, valid {len(valid)} (held-out trajectories); "
          f"{a.epochs} epochs x {upd_per_epoch} updates (accum {a.accum}) = {total} updates; "
          f"IPO beta {a.beta} (target per-token gap {1/(2*a.beta):.3f}), lr {a.lr}", flush=True)
    vl, va, vm = evaluate(policy, ref, valid, a.beta, a.step)
    print(f"[eval] update 0: val loss {vl:.5f} acc {va:.3f} margin {vm:.5f}", flush=True)
    upd = 0; t0 = time.time()
    for ep in range(a.epochs):
        order = np.random.permutation(len(train))
        for b0 in range(0, len(order), a.accum):
            idx = order[b0:b0 + a.accum]; acc_g = None; Ls, As, Ms = [], [], []
            for i in idx:
                p = train[int(i)]
                c, cm = arr(p["chosen"], p["chosen_mask"]); r, rm = arr(p["rejected"], p["rejected_mask"])
                l, g, met, _ = pair_grad(policy, ref, c, cm, r, rm, a.beta, a.step)
                acc_g = g if acc_g is None else tree_map(lambda x, y: x + y, acc_g, g)
                Ls.append(l); As.append(met["accuracies"]); Ms.append(met["margins"])
            acc_g = tree_map(lambda x: x / len(idx), acc_g)
            opt.update(policy, acc_g); mx.eval(policy.trainable_parameters(), opt.state)
            upd += 1
            el = time.time() - t0
            print(f"[train] ep {ep+1} update {upd}/{total}: loss {np.mean(Ls):.5f} acc {np.mean(As):.3f} "
                  f"margin {np.mean(Ms):.5f} | {el/60:.1f} min elapsed, ~{el/upd*(total-upd)/60:.0f} min left, "
                  f"peak {mx.get_peak_memory()/1e9:.1f} GB", flush=True)
            if upd % a.eval_every == 0 or upd == total:
                vl, va, vm = evaluate(policy, ref, valid, a.beta, a.step)
                print(f"[eval] update {upd}: val loss {vl:.5f} acc {va:.3f} margin {vm:.5f}", flush=True)
                save_adapters(policy, a.out, a.rank, a.scale, a.num_layers, tag=f"{upd:04d}_adapters")
    save_adapters(policy, a.out, a.rank, a.scale, a.num_layers)
    print(f"[done] saved {a.out}/adapters.safetensors", flush=True)

if __name__ == "__main__":
    main()
