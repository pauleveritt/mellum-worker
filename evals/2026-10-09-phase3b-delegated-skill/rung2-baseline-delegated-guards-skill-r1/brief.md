Files: ledger.py, test_ledger.py
Change: In ledger.py add a function balance(entries) that returns the sum of entry.amount for the given iterable of Entry values. In test_ledger.py add a test named test_balance that builds entries with entries_from_lines(["coffee, -3", "pay, 10"]) and asserts balance(...) == 7.
Test command: uv run --offline pytest -q (run from /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-omn9jbqj/rung2)
Do not change: nothing else. Keep Entry, entries_from_lines, and the existing test_parses_lines exactly as they are; do not touch pyproject.toml.
Done when: the test command exits 0 and you have replied with the files changed and the test output pasted verbatim.