Done via `mellum-worker`. I independently re-verified the result:

**Changes**
- `rows.py:1` — `def fetch_rows(source)` → `def load_rows(source)`
- `report.py:1` — `from rows import load_rows`
- `report.py:5` — call site updated

**Verification (run by me, not just reported)**
- `grep -rn "fetch_rows\|load_rows" .` → no `fetch_rows` matches remain; only the 3 `load_rows` references above
- `git diff --stat` → `report.py | 4 ++--`, `rows.py | 2 +-` (3 insertions, 3 deletions — exactly the three identifiers)
- Worker's own checks: `uv run --offline pytest -q` → 1 passed; `ruff check .` → all checks passed

No occurrences were skipped.