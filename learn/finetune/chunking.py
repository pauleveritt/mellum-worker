"""Bounds for scoring a long sequence in cached chunks, with no chunk too short to train through.

Each chunk (s, e) is scored on tokens s..e-1 with a KV cache, predicting targets s+1..e-1; continuation
chunks start one token back so every next-token target is predicted exactly once.

MLX runs attention for a very short query (a handful of tokens) on vector kernels that have no backward
pass ("the vector kernels do not produce a logsumexp"), so a short final chunk crashes training. A tail
shorter than MIN_CHUNK is folded into the chunk before it instead.
"""
MIN_CHUNK = 64


def chunk_bounds(n, step, min_chunk=MIN_CHUNK):
    bounds, start = [], 0
    while True:
        end = min(start + step, n)
        if 0 < n - end < min_chunk:  # the tail would be too short: take it now
            end = n
        bounds.append((max(0, start - 1), end))
        if end >= n:
            return bounds
        start = end
