Fixed via `mellum-worker`. All 4 tests pass.

**Root cause:** the totals feature was unimplemented at all three layers — `export_csv()` had no `totals` kwarg (the reported missing row), `render_rows()` had no `mark_last` support, and `column_totals()` crashed on text cells instead of returning `""`.

**Changes** (in `/private/.../rung5`):
- `render.py` — `render_rows(rows, mark_last=False)` now prefixes the last line with `TOTAL,` when `mark_last=True`.
- `export.py` — `export_csv(rows, totals=False)` appends `column_totals(rows)` and renders with `mark_last=totals`.
- `totals.py` — `column_totals()` sums numeric columns and returns `""` for columns containing non-numeric text.
- Left `exports_legacy.py` and `test_export.py` untouched, as required.

**Verification** (independent, run by me after the child finished):
```
.venv/bin/python -m pytest -q
....                                                                     [100%]
4 passed in 0.00s
```

**Process note:** the first `mellum-worker` run aborted after fixing only `totals.py` — the subagent harness kills a run when a `bash` command exits non-zero, and its initial `pytest` (naturally failing at that point) did so. I captured the partial diff and resumed the same run with a corrected protocol (finish all edits first, then run pytest as `... > file 2>&1; echo EXIT:$?; cat file` so the command exits 0). The resume completed cleanly. Everything is left as uncommitted working-tree changes; I did not commit.