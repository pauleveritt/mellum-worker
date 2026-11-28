In the repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-z1us8oqb/rung2:

1. Read ledger.py. It defines a frozen dataclass `Entry(memo: str, amount: int)` and `entries_from_lines(lines) -> list[Entry]`.
2. Add a module-level function `balance(entries)` that sums the `amount` field across the given entries and returns the total as an int. Empty input must return 0. Use a simple loop or `sum(e.amount for e in entries)`. Do not change existing code.
3. Add a test to test_ledger.py named `test_balance_sums_entries` that builds entries (e.g. via entries_from_lines(["coffee, -3", "pay, 10"]) or directly with Entry(...)) and asserts balance(...) == 7, plus an assertion that balance([]) == 0.
4. Run `pytest -q` (use the project's .venv; if plain `pytest` is not found, use `.venv/bin/pytest -q`) and confirm all tests pass.
5. Report: exact diff of what you changed and the pytest output.