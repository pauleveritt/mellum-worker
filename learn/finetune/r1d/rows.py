"""Train only a few rows of the embedding table and the language-model head.

Each wrapper keeps the original table frozen and adds a small trainable `delta` for rows start..start+n (the new
tokens). Every other row reads exactly as before, so the rest of the vocabulary cannot move. `merged()` folds the
delta back into a full weight for saving.
"""
import mlx.core as mx
import mlx.nn as nn


class RowDeltaEmbedding(nn.Module):
    def __init__(self, base, start, n):
        super().__init__()
        self.base, self.start, self.n = base, start, n
        self.delta = mx.zeros((n, base.weight.shape[1]), dtype=base.weight.dtype)

    def __call__(self, ids):
        rel = ids - self.start
        new = ((rel >= 0) & (rel < self.n))[..., None]
        return self.base(ids) + mx.where(new, self.delta[mx.clip(rel, 0, self.n - 1)], 0)

    def merged(self):
        w = self.base.weight
        return mx.concatenate([w[:self.start], w[self.start:self.start + self.n] + self.delta,
                               w[self.start + self.n:]])


class RowDeltaHead(nn.Module):
    def __init__(self, base, start, n):
        super().__init__()
        self.base, self.start, self.n = base, start, n
        self.delta = mx.zeros((n, base.weight.shape[1]), dtype=base.weight.dtype)

    def __call__(self, x):
        logits = self.base(x)
        s, e = self.start, self.start + self.n
        return mx.concatenate([logits[..., :s], logits[..., s:e] + x @ self.delta.T, logits[..., e:]], axis=-1)

    def merged(self):
        w = self.base.weight
        return mx.concatenate([w[:self.start], w[self.start:self.start + self.n] + self.delta,
                               w[self.start + self.n:]])
