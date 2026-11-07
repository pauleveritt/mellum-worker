Done. `mellum-worker` completed the rename and I verified it independently.

**Changes**
- `rows.py`: `fetch_rows` → `load_rows` (function definition)
- `report.py`: import and call site updated

**Verification**
- `grep -rn "fetch_rows" .` → no matches (exit 1)
- `git diff` → only the intended 3 lines changed
- `uv run pytest -q` → `1 passed`