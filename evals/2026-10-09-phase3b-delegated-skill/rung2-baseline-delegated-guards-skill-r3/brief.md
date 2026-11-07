Repo cwd is the project root (ledger.py, test_ledger.py). Bounded change, only touch these two files.

1. In ledger.py, add a function `balance(entries)` that returns the sum of the `amount` field of all entries (use sum()). Keep existing style; no type annotations were used, so keep it consistent and simple.
2. In test_ledger.py, add a test named `test_balance` that builds entries via entries_from_lines(["coffee, -3", "pay, 10"]) and asserts balance(...) == 7. Also assert balance([]) == 0.
3. Run the tests with `./.venv/bin/python -m pytest -q` and confirm they pass.

Report: exact diff of both files, the pytest command output, and any uncertainty. Do not add dependencies, do not reformat unrelated code.