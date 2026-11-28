"""Checkpoint and resume for dpo_native_train.py, so a crash costs one update, not the run.

`plan_updates` is the training order as a list (epoch, update, pair indices): the same seed always gives the
same plan, so a resumed run takes exactly the batches the crashed run had left. `save_checkpoint` writes the
trainable weights, the optimizer state and the update number after every update; `load_checkpoint` restores
all three.
"""
import json
from pathlib import Path

import numpy as np


def plan_updates(n_pairs, accum, epochs, seed, start=0):
    rng, plan, upd = np.random.RandomState(seed), [], 0
    for ep in range(epochs):
        order = rng.permutation(n_pairs)
        for b0 in range(0, n_pairs, accum):
            upd += 1
            plan.append((ep, upd, [int(i) for i in order[b0:b0 + accum]]))
    return plan[start:]


def save_checkpoint(out, trainable, opt, update):
    import mlx.core as mx
    from mlx.utils import tree_flatten

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    mx.save_safetensors(str(out / "resume_weights.safetensors"), dict(tree_flatten(trainable)))
    mx.save_safetensors(str(out / "resume_optimizer.safetensors"), dict(tree_flatten(opt.state)))
    (out / "resume.json").write_text(json.dumps({"update": update}) + "\n")


def load_checkpoint(out, model, opt):
    """Restore weights and optimizer state; returns the number of updates already done."""
    import mlx.core as mx
    from mlx.utils import tree_unflatten

    out = Path(out)
    model.load_weights(str(out / "resume_weights.safetensors"), strict=False)
    opt.state = tree_unflatten(list(mx.load(str(out / "resume_optimizer.safetensors")).items()))
    return json.loads((out / "resume.json").read_text())["update"]
