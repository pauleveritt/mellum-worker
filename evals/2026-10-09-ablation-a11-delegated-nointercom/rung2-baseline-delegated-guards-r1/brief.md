Objective: add a `balance(entries)` function to ledger.py plus a test for it, using test-first (TDD).

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-pvv7z72v/rung2
You are the only writer. Edit ONLY ledger.py and test_ledger.py. Do not touch pyproject.toml, .pi/, or .venv/.

Contract:
- `balance(entries)` accepts an iterable of `Entry` and returns the sum of `entry.amount` as an int.
- `balance([]) == 0` (empty iterable -> 0).
- Existing `Entry` and `entries_from_lines` behavior must not change.

Steps (in this order):
1. RED: Add `test_balance` to test_ledger.py that imports `balance` and asserts `balance([Entry("coffee", -3), Entry("pay", 10)]) == 7` and `balance([]) == 0`. Run `.venv/bin/pytest -q test_ledger.py` and confirm it FAILS (ImportError or NameError). Capture the exact output.
2. GREEN: Add the minimal `balance` implementation to ledger.py.
3. Run `.venv/bin/pytest -q` and confirm ALL tests pass. Capture the exact output.

Stop when tests pass. Report: files changed, the exact pytest output from the failing run and the passing run, and the final `balance` source. Do not commit.