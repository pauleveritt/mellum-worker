Done via `mellum-worker`, verified independently.

**Changes** (3 lines, no other behavior touched):
- `rows.py`: `def fetch_rows(source)` → `def load_rows(source)`
- `report.py`: import `from rows import load_rows`
- `report.py`: call site `r in load_rows(source)`

**Verification I ran myself:**
- `grep -rn fetch_rows .` → no matches (exit 1)
- `python -m pytest -q` → `1 passed in 0.00s`
- `git diff` shows only the rename hunks; nothing committed.