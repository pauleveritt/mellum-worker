Done — `mellum-worker` completed the rename, and I verified it independently.

**Changes (2 files, 3 insertions / 3 deletions):**
- `rows.py:1` — `def fetch_rows` → `def load_rows`
- `report.py:1` — `from rows import fetch_rows` → `load_rows`
- `report.py:5` — call site → `load_rows(source)`

**Verification (run by me, not the child):**
- `grep -rn "fetch_rows" .` → no matches (exit 1)
- `grep -rn "load_rows" .` → 3 expected matches
- `git diff` → clean, only the intended identifier renames; no formatting or behavior changes
- `uv run pytest -q` → `1 passed`

Note: `test_report.py` never referenced `fetch_rows`, so no test change was needed.