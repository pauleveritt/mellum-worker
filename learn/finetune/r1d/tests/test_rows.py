"""Training only the new tokens' rows: every other embedding and head row stays exactly as it was."""
import sys
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn

sys.path.insert(0, str(Path(__file__).parent.parent))
from rows import RowDeltaEmbedding, RowDeltaHead  # noqa: E402

mx.random.seed(0)


def test_embedding_changes_only_new_ids():
    base = nn.Embedding(10, 4); base.freeze()
    emb = RowDeltaEmbedding(base, start=7, n=2)
    emb.delta = mx.ones((2, 4))
    ids = mx.array([[0, 6, 7, 8, 9]])
    out, ref = emb(ids), base(ids)
    assert mx.array_equal(out[0, [0, 1, 4]], ref[0, [0, 1, 4]])
    assert mx.allclose(out[0, [2, 3]], ref[0, [2, 3]] + 1)


def test_head_changes_only_new_columns():
    base = nn.Linear(4, 10, bias=False); base.freeze()
    head = RowDeltaHead(base, start=7, n=2)
    head.delta = mx.ones((2, 4))
    x = mx.random.normal((3, 4))
    out, ref = head(x), base(x)
    keep = [0, 1, 2, 3, 4, 5, 6, 9]
    assert mx.array_equal(out[:, keep], ref[:, keep])
    assert mx.allclose(out[:, 7:9], ref[:, 7:9] + x.sum(-1, keepdims=True))


def test_only_the_deltas_are_trainable_and_merging_matches_the_wrapped_output():
    base_e, base_h = nn.Embedding(10, 4), nn.Linear(4, 10, bias=False)
    base_e.freeze(); base_h.freeze()
    emb, head = RowDeltaEmbedding(base_e, 7, 2), RowDeltaHead(base_h, 7, 2)
    assert set(dict(nn.utils.tree_flatten(emb.trainable_parameters()))) == {"delta"}
    assert set(dict(nn.utils.tree_flatten(head.trainable_parameters()))) == {"delta"}
    emb.delta, head.delta = mx.random.normal((2, 4)), mx.random.normal((2, 4))
    ids, x = mx.array([[1, 7, 8]]), mx.random.normal((2, 4))
    assert mx.allclose(emb.merged()[ids], emb(ids), atol=1e-6)
    assert mx.allclose(x @ head.merged().T, head(x), atol=1e-5)
    assert mx.array_equal(emb.merged()[:7], base_e.weight[:7]) and mx.array_equal(head.merged()[9:], base_h.weight[9:])
