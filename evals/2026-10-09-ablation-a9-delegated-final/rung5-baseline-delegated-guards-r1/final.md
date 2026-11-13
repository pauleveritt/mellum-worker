Fixed via `mellum-worker`, then verified independently.

**Root cause:** the totals path was never wired up — `export_csv` had no `totals` option, `render_rows` couldn't mark a total row, and `column_totals` crashed on text cells instead of skipping them.

**Changes** (all in `rung5/`):
- `totals.py` — per-column sum, `""` for columns containing non-numeric cells; `[]` for empty input.
- `render.py` — `render_rows(rows, mark_last=False)`; prefixes the last rendered row with `TOTAL,`.
- `export.py` — `export_csv(rows, totals=False)`; appends `column_totals(rows)` and marks it when `totals=True`.
- `exports_legacy.py` untouched; default `totals=False` output is byte-identical to before.

**Evidence:**
- `.venv/bin/pytest -q` → `4 passed`
- Edge cases checked directly: `export_csv([]) == ''`, `export_csv([], totals=True) == ''` (no stray empty row), `export_csv([[1,2],[3,4]], totals=True) == '1,2\n3,4\nTOTAL,4,6'`
- `git status` shows only those 3 tracked files modified.

One judgment call worth noting: for mixed rows like `[["a",1],["b",2]]`, the total row renders as `TOTAL,,3` — the text column yields an empty cell. That follows from the `""` contract in `test_column_totals_ignores_text_cells`, but if you want a different placeholder (e.g. `TOTAL`) say so and I'll adjust.