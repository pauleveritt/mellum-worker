Done — renamed `fetch_rows` → `load_rows` via `mellum-worker`, then independently verified.

**Changes**
- `rows.py`: `def load_rows(source)`
- `report.py`: import + call site

**Independent verification (run by me, not just the child)**
- `grep -rn "fetch_rows" .` → no matches (exit 1)
- `git diff --stat` → only those 2 files, 3 insertions / 3 deletions
- `uv run pytest -q` → `1 passed in 0.00s`

Nothing else was touched, and no commit was made.