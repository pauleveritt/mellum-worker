Task: add a `balance()` function to the Python ledger module in the current working directory (/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-lhrdnq2f/rung2), with a pytest test.

Current state (read the files yourself to confirm):
- ledger.py defines a frozen dataclass `Entry(memo: str, amount: int)` and `entries_from_lines(lines)`.
- test_ledger.py has one test, test_parses_lines, importing `Entry, entries_from_lines` from `ledger`.

Required work:
1. In ledger.py add `def balance(entries):` that returns the sum of the `amount` field of every entry in the iterable `entries`. An empty iterable must return 0 (use `sum(...)` with a start value or equivalent). Do not change `Entry` or `entries_from_lines`.
2. In test_ledger.py add a test named `test_balance` that imports and exercises `balance`. Cover both a non-empty case (e.g. entries summing to a nonzero value, including a negative amount) and the empty case returning 0. Keep the existing test passing; do not modify the existing test.

Constraints:
- Only edit ledger.py and test_ledger.py. Touch no other files.
- Match the existing code style; no new dependencies, no type stubs or docstring boilerplate beyond a short one-line docstring if natural.
- Run the test suite with `pytest -q` (fall back to `.venv/bin/pytest -q` if `pytest` is not on PATH) from the working directory. Do not use `uv` unless pytest is missing entirely.

Acceptance criteria (must all hold when you report back):
- `balance([])` == 0 and `balance(entries)` sums amounts.
- `pytest -q` passes with at least 2 tests, 0 failures.
- Report: exact commands run, raw test output, and the final contents of both changed files.