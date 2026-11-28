Verified independently.

- `rows.py`: `def load_rows(source)` ✓
- `report.py`: `from rows import load_rows` and call site updated ✓
- `grep -rn "fetch_rows" .` → no matches (exit 1) ✓
- `uv run pytest -q` → `1 passed` ✓
- Diff limited to `report.py` (2 lines) and `rows.py` (1 line), no other behavior changes.

Rename complete.