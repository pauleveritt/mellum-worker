Done. Delegated to `mellum-worker`, then verified independently.

**Rename complete: `fetch_rows` → `load_rows`**

- `rows.py:1` — definition renamed
- `report.py:1` — import renamed
- `report.py:5` — call site renamed

**Verification (run by me, not just the child):**
- `grep -rn "fetch_rows" . --include="*.py"` → no matches
- `grep -rn "load_rows" . --include="*.py"` → definition, import, call site
- `uv run pytest -q` → `1 passed in 0.00s`

The diff touches only the three rename sites; no other behavior changed.