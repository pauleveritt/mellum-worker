Done. `fetch_rows` → `load_rows` everywhere.

**mellum-worker:** first run (fd4fca7f) failed with no edits — it planned the changes but exhausted output while thinking and stopped without calling `edit`. A single more directive retry (2199a141) completed.

**Verified independently:**
- `rows.py`: `def load_rows(source):`
- `report.py`: import + call site updated
- `grep -rn fetch_rows` → no matches
- `python -m pytest -q` → `1 passed`

Diff is exactly 3 lines, no other behavior changed.