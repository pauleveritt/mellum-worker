Done and independently verified.

**Change** — `fetch_rows` → `load_rows` (3 references, exact diff above):

| File | Change |
|---|---|
| `rows.py:1` | `def load_rows(source):` |
| `report.py:1` | `from rows import load_rows` |
| `report.py:5` | `load_rows(source)` |

**Verification I ran myself (not just the child's claims):**
- `grep -rn fetch_rows` → no matches (exit 1)
- `grep -rn load_rows` → exactly the 3 expected sites
- `.venv/bin/python -m pytest -q` → `1 passed`
- `git status` → only `report.py` and `rows.py` modified; `test_report.py` and `pyproject.toml` untouched

**Two caveats worth knowing:**
1. The harness marked the `mellum-worker` run as **failed** (`Acceptance rejected: Structured acceptance report not found`), even though the gate command (`pytest`) passed and the work is correct. That's a reporting-shape technicality in the child's final message, not a code failure. The output artifact is at `/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/pi-subagents-uid-501/artifacts/b2f973a8-beeb-42af-9352-cc0c2c0f3995_mellum-worker_0_output.md`.
2. Changes are unstaged and working-tree only — I did not commit. Say the word if you want a commit.