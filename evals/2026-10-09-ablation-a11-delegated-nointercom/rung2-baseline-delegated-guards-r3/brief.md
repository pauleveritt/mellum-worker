Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-78t667yj/rung2

Goal: add a `balance()` function that sums the entries, with a test.

Existing files:
- ledger.py defines a frozen dataclass `Entry(memo: str, amount: int)` and `entries_from_lines(lines)`.
- test_ledger.py has pytest tests importing `from ledger import Entry, entries_from_lines`.

Follow TDD strictly:
1. First add a failing test to test_ledger.py:
   `from ledger import Entry, entries_from_lines, balance`
   def test_balance_sums_amounts():
       entries = [Entry("coffee", -3), Entry("pay", 10), Entry("tea", -4)]
       assert balance(entries) == 3
2. Run `uv run pytest -q` and confirm the test fails because `balance` does not exist (capture the failure output).
3. Implement in ledger.py:
   def balance(entries):
       return sum(entry.amount for entry in entries)
   Match the existing plain style (no type annotations were used on functions; you may keep them off).
4. Run `uv run pytest -q` again and confirm all tests pass.
5. Run `uv run pytest -q` a final time and copy the exact output.

Constraints:
- Only modify ledger.py and test_ledger.py. Do not touch other files.
- Do not modify existing tests or `entries_from_lines`.
- Use `uv run pytest -q` (pytest is the dev dependency; do not use `rtk` or `il`).

Report back: the final contents of ledger.py, the exact final pytest output, and the commands you ran with their pass/fail results.