"""The training loss counts the completion only, and the marker check reads the right positions."""
import sys
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
from mlx_lm.models.qwen2 import Model, ModelArgs

sys.path.insert(0, str(Path(__file__).parent.parent))
from train_sft import completion_loss, marker_hits, pick_examples, switchable_checkpoint  # noqa: E402

mx.random.seed(0)
ARGS = ModelArgs(model_type="qwen2", hidden_size=16, num_hidden_layers=1, intermediate_size=32, num_attention_heads=2,
                 rms_norm_eps=1e-6, vocab_size=20, num_key_value_heads=1, tie_word_embeddings=False)


def test_loss_is_mean_cross_entropy_over_completion_tokens_only():
    model = Model(ARGS)
    ids, n_prompt = mx.array([1, 2, 3, 4, 5, 6, 7]), 4
    logits = model(ids[None, :-1])[0]
    want = nn.losses.cross_entropy(logits[n_prompt - 1:], ids[n_prompt:]).mean()
    assert mx.allclose(completion_loss(model, ids, n_prompt), want, atol=1e-5)


def test_marker_hits_counts_marker_targets_the_model_ranks_first():
    logits = mx.zeros((4, 20))
    logits = logits.at[1, 17].add(5.0).at[3, 2].add(5.0)
    targets = mx.array([3, 17, 9, 17])  # markers (id 17) at positions 1 and 3; only position 1 is ranked first
    assert marker_hits(logits, targets, marker=17) == (1, 2)


def test_a_resumed_run_takes_exactly_the_examples_the_first_run_skipped():
    import random
    rows = [{"i": i} for i in range(50)]
    first = pick_examples(rows, seed=0, start=0, count=20)
    rest = pick_examples(rows, seed=0, start=20, count=0)
    ref = list(rows); random.seed(0); random.shuffle(ref)  # what the first v2 run did
    assert first == ref[:20] and rest == ref[20:]
    assert len(rest) == 30 and not {r["i"] for r in first} & {r["i"] for r in rest}
    assert rows == [{"i": i} for i in range(50)]  # the caller's list is not shuffled in place


def test_checkpointing_switches_per_example_and_leaves_the_gradients_unchanged(monkeypatch):
    """Checkpointing reruns each layer's forward in the backward pass: worth it only for long examples."""
    model = Model(ARGS); model.freeze(); model.model.layers[0].self_attn.q_proj.unfreeze()
    ids = mx.array([1, 2, 3, 4, 5, 6, 7])
    grad = lambda: nn.value_and_grad(model, completion_loss)(model, ids, 4)[1]
    plain = grad()
    calls = []
    real = mx.checkpoint
    monkeypatch.setattr(mx, "checkpoint", lambda f: calls.append(1) or real(f))
    state, restore = switchable_checkpoint(model.model.layers[0])
    try:
        state["on"] = False
        off = grad()
        assert calls == []
        state["on"] = True
        on = grad()
        assert calls
    finally:
        restore()
    for g in (off, on):
        assert all(mx.allclose(a, b, atol=1e-6) for a, b in zip(nn.utils.tree_flatten(g), nn.utils.tree_flatten(plain))
                   for a, b in [(a[1], b[1])])
