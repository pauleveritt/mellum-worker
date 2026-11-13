Done — `mellum-worker` performed the rename, and I verified it independently.

**Changed files (2):**
- `rows.py:1` — `def fetch_rows(source):` → `def load_rows(source):`
- `report.py:1` — `from rows import fetch_rows` → `from rows import load_rows`
- `report.py:5` — call site → `load_rows(source)`

**Verification (my own commands, not the child's report):**
- `grep -rn "fetch_rows" .` → no matches (exit 1)
- `grep -rn "load_rows" --include="*.py" .` → 3 expected occurrences
- `uv run pytest -q` → `1 passed in 0.00s`
- `git diff --stat` → 2 files, 3 insertions, 3 deletions; nothing else touched

Not committed, as instructed. `.pi/` is untracked session state, unrelated to the change.