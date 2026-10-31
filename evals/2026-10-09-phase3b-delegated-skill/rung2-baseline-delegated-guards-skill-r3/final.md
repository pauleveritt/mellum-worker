**mellum-worker** delivered, then I verified and fixed one style issue.

**Changes**
- `ledger.py`: added `balance(entries)` → `sum(entry.amount for entry in entries)`
- `test_ledger.py`: added `test_balance` (mixed signs → 7, empty → 0), updated import

**Verification (parent-run, authoritative)**
- `./.venv/bin/python -m pytest -q` → `2 passed in 0.00s`
- Fixed the child's single blank line before the module-level `def` to two (E302).

**Notes**
- The runner reported `Acceptance rejected: Structured acceptance report not found` and the mission as `failed`, even though the child's output contained a well-formed acceptance report and the work landed. That looks like a runner/acceptance gate artifact, not a work failure — the gate command's result isn't in the returned payload, so I re-ran pytest myself.
- Nothing is staged (`noStagedFiles: true`); changes are unstaged in `rung2`.