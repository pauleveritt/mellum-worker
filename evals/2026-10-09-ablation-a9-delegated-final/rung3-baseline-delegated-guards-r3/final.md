Done — delegated to `mellum-worker` and verified independently.

**Changes** (`git diff`, 3 lines, no collateral edits):

| File | Change |
|---|---|
| `rows.py:1` | `def fetch_rows(source):` → `def load_rows(source):` |
| `report.py:1` | `from rows import fetch_rows` → `from rows import load_rows` |
| `report.py:5` | `fetch_rows(source)` → `load_rows(source)` |

**Verification I ran (not just the worker's word):**
- `rg -n "fetch_rows" .` → no matches
- `git diff --stat` → `report.py | 4 ++--`, `rows.py | 2 +-` (confirms only the intended lines)
- `uv run pytest -q` → `1 passed`

One caveat worth flagging: the worker's self-reported diff showed a spurious added blank line in `report.py` that is **not** in the actual file — its prose diff was slightly fabricated, while the real on-disk edits and its own command log were correct. I caught this by checking `git diff` directly rather than trusting the report. Rename itself is correct and complete.