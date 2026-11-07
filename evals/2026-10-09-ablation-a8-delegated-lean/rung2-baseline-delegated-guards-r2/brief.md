Repository: the current working directory, the Python project "ledger".

What exists:
- ledger.py defines a frozen dataclass Entry with fields memo (a str) and amount (an int), plus the function entries_from_lines(lines).
- test_ledger.py holds pytest tests.
- pyproject.toml configures pytest.

Task: add a function balance(entries) to ledger.py that returns the sum of the amount field of every Entry in the given sequence of entries. Add a test for balance in test_ledger.py.

Test command: run `uv run --offline pytest -q` in the current working directory. The task is complete only when that command exits 0.

When done, reply with the files changed and the test output.