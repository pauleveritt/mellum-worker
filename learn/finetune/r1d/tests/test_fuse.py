"""Folding the trained LoRA and new-row deltas into plain weights gives the same outputs as the wrapped model."""
import sys
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from mlx_lm.tuner.lora import LoRALinear

sys.path.insert(0, str(Path(__file__).parent.parent))
from fuse import fuse_weights  # noqa: E402
from rows import RowDeltaEmbedding, RowDeltaHead  # noqa: E402

mx.random.seed(0)


def test_fused_lora_linear_matches_the_adapter():
    base = nn.Linear(6, 5, bias=False)
    lora = LoRALinear.from_base(base, r=2, scale=2.0)
    lora.lora_b = mx.random.normal(lora.lora_b.shape)
    x = mx.random.normal((3, 6))
    weights = {"model.layers.0.mlp.up_proj.weight": np.array(base.weight)}
    adapters = {"model.layers.0.mlp.up_proj.lora_a": np.array(lora.lora_a),
                "model.layers.0.mlp.up_proj.lora_b": np.array(lora.lora_b)}
    fused = fuse_weights(weights, adapters, scale=2.0, start=0)
    w = mx.array(fused["model.layers.0.mlp.up_proj.weight"])
    assert np.allclose(np.array(x @ w.T), np.array(lora(x)), atol=1e-5)


def test_fused_rows_match_the_wrappers_and_leave_other_rows_alone():
    emb, head = nn.Embedding(10, 4), nn.Linear(4, 10, bias=False)
    we, wh = RowDeltaEmbedding(emb, 7, 2), RowDeltaHead(head, 7, 2)
    we.delta, wh.delta = mx.random.normal((2, 4)), mx.random.normal((2, 4))
    weights = {"model.embed_tokens.weight": np.array(emb.weight), "lm_head.weight": np.array(head.weight)}
    adapters = {"model.embed_tokens.delta": np.array(we.delta), "lm_head.delta": np.array(wh.delta)}
    fused = fuse_weights(weights, adapters, scale=2.0, start=7)
    fe, fh = fused["model.embed_tokens.weight"], fused["lm_head.weight"]
    ids = mx.array([0, 6, 7, 8, 9])
    assert np.allclose(fe[np.array(ids)], np.array(we(ids)), atol=1e-6)
    x = mx.random.normal((3, 4))
    assert np.allclose(np.array(x) @ fh.T, np.array(wh(x)), atol=1e-5)
    assert np.array_equal(fe[:7], np.array(emb.weight)[:7]) and np.array_equal(fh[9:], np.array(head.weight)[9:])


def test_an_adapter_with_no_matching_weight_is_an_error():
    try:
        fuse_weights({}, {"model.layers.0.mlp.up_proj.lora_a": np.zeros((2, 1)),
                          "model.layers.0.mlp.up_proj.lora_b": np.zeros((1, 2))}, scale=1.0, start=0)
    except KeyError:
        return
    raise AssertionError("missing base weight was ignored")
