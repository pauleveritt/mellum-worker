Bounded coding task. Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-tb4yul_e/rung2 (Python 3.14, pytest).

Objective: add a `balance()` function to ledger.py that sums the amounts of a sequence of Entry objects, plus a test for it.

Context:
- `ledger.py` currently defines a frozen dataclass `Entry(memo: str, amount: int)` and `entries_from_lines(lines)`.
- `test_ledger.py` currently has one test, `test_parses_lines`, importing `from ledger import Entry, entries_from_lines`.
- pyproject.toml sets dev dep pytest and `testpaths = ["."]`.

Required changes (only these two files):
1. ledger.py: add `def balance(entries):` returning the sum of `e.amount` for entries in the input. It must work with a list of Entry and return 0 for an empty input. Keep it a plain function; do not add classes or imports.
2. test_ledger.py: add a test `test_balance` (or equivalent) covering at least a non-empty case with mixed positive/negative amounts and the empty case.

Approach: write the failing test first, then implement `balance()`, then run the suite.

Acceptance/validation: run `cd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-tb4yul_e/rung2 && python -m pytest -q` and confirm all tests pass. Use the repo's .venv if present (e.g. `.venv/bin/python -m pytest -q`).

Authority: you may edit only ledger.py and test_ledger.py. No new files, no dependency changes, no git commits.

Report: files changed, the final code of `balance()`, the exact pytest command and its output, and any blockers. Stop and report instead of guessing if the codebase contradicts this brief.