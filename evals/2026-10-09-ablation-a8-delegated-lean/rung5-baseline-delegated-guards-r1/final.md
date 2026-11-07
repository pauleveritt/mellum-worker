Done — all 4 tests pass and the protected files are untouched.

## Result

The export now includes the totals row. `export_csv(..., totals=True)`:

```
1,2
3,4
TOTAL,4,6
```

**Files changed** (by `mellum-worker`):
- `render.py` — `render_rows(rows, mark_last=False)`; prefixes the last row with `TOTAL,`.
- `export.py` — `export_csv(rows, totals=False)`; appends `column_totals(rows)` and renders with `mark_last=True`.
- `totals.py` — `column_totals` now skips text cells, returning `""` for an all-text column.

**Verification** (run by me, parent): `.venv/bin/pytest -q` → `4 passed in 0.00s`. `test_export.py`, `exports_legacy.py`, and `pyproject.toml` are unmodified.

## Lane notes (transparency)

`mellum-worker` needed 3 attempts — the local Mellum model kept exhausting its output budget on `thinking` and terminating with an empty message:
1. `62484c15…` — failed "no output" after editing only `totals.py`; partial diff captured.
2. `c945d3fb…` (resume of #1) — same failure; `render.py`/`export.py` still unchanged.
3. Fresh run with `--model omlx/Mellum2.1-12B-A2.5B-Thinking-6bit:low` and exact file contents supplied — completed, `4 passed`.

Minor nit: `render.py` and `export.py` now lack a trailing newline (from the `write` tool). Say the word and I'll add them.