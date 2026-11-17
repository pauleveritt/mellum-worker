Done and verified independently.

**Result: 4 passed in 0.00s** (`.venv/bin/python -m pytest -q`)

Changes (test_export.py untouched):

- `totals.py` — `column_totals` now returns `""` for columns containing non-numeric cells, sums numeric columns.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last rendered row with `TOTAL,` when set.
- `export.py` — `export_csv(rows, totals=False)` appends a `TOTAL,` row from `column_totals` when set.

Process note: the first mellum-worker run stopped early after editing only `totals.py` (model emitted an empty response, run failed as "no output"). I revived run `88f5350b` with the explicit remaining steps; the resumed run completed the rest. Both the child's report and my own `git diff` + pytest run agree.