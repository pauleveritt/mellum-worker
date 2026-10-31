Done — delegated to `mellum-worker` and independently verified.

**Rename complete: `fetch_rows` → `load_rows`**

| Check | Result |
|---|---|
| `grep -rn "fetch_rows"` | no matches (exit 1) |
| `grep -rn "load_rows"` | 3 hits: `rows.py:1`, `report.py:1`, `report.py:5` |
| `uv run pytest -q` | `1 passed` |
| `git diff --stat` | `report.py` 2 changed, `rows.py` 1 changed — nothing else |

Changed:
- `rows.py` — `def load_rows(source):`
- `report.py` — `from rows import load_rows` and the call site

No residual risk: 3 of 3 occurrences renamed, no collateral edits, tests green.