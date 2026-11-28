# 0001: Training data is committed, sectioned under 45 MB, never rebuilt in place

- **Date:** 2026-11-25 (sectioning 2026-11-26)
- **Status:** Accepted

## Context

The early pair sets were git-ignored, and the data behind one adapter (onpolicy21) was lost with its weights.
Later a rebuild into an existing folder overwrote a set. Single `train.jsonl` files grew past GitHub's limits.

## Decision

- Every training set under `learn/finetune/` is committed with a `SOURCE.md` saying how it was built (sources,
  filters, caps, the exact command and its output).
- Builders refuse an existing output folder: each build is a new versioned folder (`_v2`, `_v3`...).
- Sets are written by `pairs_io.write_pairs` as `<split>.<section>.<NN>.jsonl`, every file under 45 MB, rows
  carrying their position so reading restores the exact order. `tests/test_pairs_io.py` fails on any tracked
  file over 45 MB.
- Each trained adapter gets a `MANIFEST.json` (data hashes, base, settings, package versions, training log).
- Adapters and GGUFs stay out of git.

## Consequences

Any tune can be rebuilt from the repo plus the run traces. The traces in `runs/` (about 34 GB, git-ignored)
are the only way to rebuild a set from scratch and still need an off-machine backup.

## Evidence

`learn/finetune/data_*/SOURCE.md`, `learn/finetune/models/*/MANIFEST.json`, `tests/test_pairs_io.py`.
