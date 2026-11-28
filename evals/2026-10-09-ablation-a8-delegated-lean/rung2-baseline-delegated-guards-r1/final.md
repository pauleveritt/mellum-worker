Done, delegated to `mellum-worker` and verified by me afterward.

**What the child produced**
- `ledger.py`: `def balance(entries): return sum(e.amount for e in entries)` — empty iterable yields `0`; `Entry`/`entries_from_lines` untouched.
- `test_ledger.py`: `test_balance` covering `[Entry("fee", 10), Entry("refund", -5)] == 5` and `balance([]) == 0`; existing test unchanged.

**Verification I ran myself (not just the child's report)**
- `pytest -q` → `2 passed in 0.00s`
- `git diff` → only `ledger.py` and `test_ledger.py` changed
- Found and fixed a lint/format nit the child left (`ruff check` I001 + missing second blank line): `ruff format` + `ruff check --fix`
- Final: `ruff format --check` → 3 files formatted; `ruff check` → All checks passed!; `pytest -q` → 2 passed

Changes are uncommitted on the current branch — say the word if you want them committed.