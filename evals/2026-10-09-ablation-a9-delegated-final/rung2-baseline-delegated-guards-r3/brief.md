Bounded TDD task in the current repo (/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-436p_veo/rung2).

Goal: add a `balance()` function to ledger.py that sums the amounts of a sequence of Entry objects, and cover it with a test in test_ledger.py.

Steps:
1. Read ledger.py and test_ledger.py.
2. Write the failing test FIRST in test_ledger.py: import balance, and assert balance([Entry("coffee", -3), Entry("pay", 10)]) == 7. Also
cover the empty case: balance([]) == 0.
3. Run `pytest` (use the project venv if needed, e.g. `.venv/bin/pytest` or `uv run pytest`) and confirm the new test fails for the right reason (balance not defined).
4. Implement `balance(entries)` in ledger.py: return sum(entry.amount for entry in entries).
5. Re-run `pytest` and confirm all tests pass.
6. Touch nothing else; do not reformat unrelated code.

Report: files changed, the exact test command run, and the final pytest output. If pytest cannot run, say exactly why instead of claiming success.