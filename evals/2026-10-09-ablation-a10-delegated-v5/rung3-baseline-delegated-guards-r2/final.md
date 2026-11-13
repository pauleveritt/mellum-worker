Done. Delegated to **mellum-worker** (run `c7b7e017`), then verified independently.

**Changed files**
- `rows.py:1` — `def fetch_rows` → `def load_rows`
- `report.py:1` — `from rows import fetch_rows` → `from rows import load_rows`
- `report.py:5` — call site `fetch_rows(source)` → `load_rows(source)`

**Verification (run by me, not just the child)**
- `grep -rn fetch_rows` across the repo → **no matches**
- `load_rows` present at all three expected sites
- `git diff` shows only the rename, no other edits
- `.venv/bin/python -m pytest -q` → **1 passed**

Note: `test_report.py` references `report`, not the renamed symbol, so it needed no change.