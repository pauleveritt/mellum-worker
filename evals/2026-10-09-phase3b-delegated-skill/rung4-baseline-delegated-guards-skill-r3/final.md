Done. `mellum-worker` made the failing test pass.

**Result:** `4 passed` (was 3 failed, 1 passed), independently verified with `.venv/bin/python -m pytest -q`.

**Changes:**
- `totals.py` — `column_totals` now skips non-numeric cells; a column with no numbers yields `""` → `["", 3]`.
- `render.py` — `render_rows(rows, mark_last=False)` prepends a `TOTAL` cell to the last row when `mark_last=True`.
- `export.py` — `export_csv(rows, totals=False)` appends a `TOTAL`-marked totals row when `totals=True`; default output unchanged.

**Process note:** the first `mellum-worker` run hit a model cold-start (empty response) after partially fixing `totals.py`. I captured the partial diff, scoped a same-protocol retry to the remaining two files, and it completed cleanly. Test file was not modified.

Untracked `.pi/` remains in the worktree (harness dir, not part of the fix). No commit made.