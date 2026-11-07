Delegated to `mellum-worker`, then verified independently.

**Result: 4 passed** (baseline was 3 failed, 1 passed). The missing totals row is now implemented.

Changes (28 insertions, 5 deletions across 3 files — `test_export.py` and `exports_legacy.py` untouched):

- `render.py` — `render_rows(rows, mark_last=False)`: prefixes the last rendered row with `TOTAL,` when requested; default output unchanged.
- `totals.py` — `column_totals`: now skips non-numeric cells, yielding `""` for a column with no numbers instead of raising `TypeError`; still `[]` for empty input.
- `export.py` — `export_csv(rows, totals=False)`: appends a `column_totals` row marked `TOTAL,` when `totals=True`; default output unchanged.

Verified behavior:
```
export_csv([[1,2],[3,4]])            -> '1,2\n3,4'
export_csv([[1,2],[3,4]], totals=True) -> '1,2\n3,4\nTOTAL,4,6'
column_totals([['a',1],['b',2]])     -> ['', 3]
```

Residual risk (minor, untested/unspecified): `export_csv([], totals=True)` returns `"TOTAL,"`, since an empty input's totals row renders empty. Not covered by the spec or tests — flagging rather than silently changing behavior.