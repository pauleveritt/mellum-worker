The failing tests have been fixed and now all tests pass:

```
$ uv run --offline pytest -q
....
4 passed in 0.01s
```

Changes made:
1. `totals.py`: Updated `column_totals` to handle non-numeric values gracefully.
2. `render.py`: Modified `render_rows` to accept `mark_last` argument and mark the last row with "TOTAL".
3. `export.py`: Updated `export_csv` to accept `totals` argument, compute total row using `column_totals`, and append it.

The task is complete.