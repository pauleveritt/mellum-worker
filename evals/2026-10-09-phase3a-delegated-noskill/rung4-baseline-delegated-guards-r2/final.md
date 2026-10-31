Done. `mellum-worker` fixed the three failures.

**Outcome:** 4 passed (was 3 failed, 1 passed). `test_export.py` was not modified.

**Changes made by the worker** (in `/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-uo9fh_d8/rung4`):
- `totals.py` — `column_totals` now skips non-numeric cells and returns `""` for all-text columns.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL`.
- `export.py` — `export_csv(rows, totals=False)` appends a totals row via `column_totals` + `mark_last=True`.

**Process note:** the first worker run stopped early after only fixing `totals.py` (empty response, exit 1). I resumed the same run (`8ef03859…` → revived as `5bf46a41…`) rather than switching agents; the resumed run finished the remaining two files. I then independently re-ran pytest and reviewed the diff, confirming all 4 tests pass and the spec file is untouched.

Verification command/output:
```
$ .venv/bin/python -m pytest -q
....                                                                     [100%]
4 passed in 0.00s
```