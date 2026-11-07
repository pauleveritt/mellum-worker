Objective: add a `balance()` function to ledger.py that returns the sum of the `amount` fields of the entries, and add a pytest test for it in test_ledger.py.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-pp_z8cy3/rung2 (already your working directory).

Relevant files:
- ledger.py — currently defines the frozen dataclass `Entry(memo, amount)` and `entries_from_lines(lines)`.
- test_ledger.py — currently imports `Entry, entries_from_lines` from ledger and has one test.

Contract for the new function:
```python
def balance(entries):
    ...
```
It takes an iterable of `Entry` objects and returns the integer sum of their `amount` values (negative amounts reduce the balance). Empty input returns 0.

Authority / edit boundary: you may edit ONLY ledger.py and test_ledger.py. Do not touch .pi/, pyproject.toml, uv.lock, or any other file.

Success criteria:
1. `balance` exists in ledger.py with the contract above (no name change, no extra required arguments).
2. test_ledger.py gains a pytest test that calls `balance` on a list containing at least one negative amount and asserts the correct total (and that `balance([]) == 0`).
3. The test command `uv run --offline pytest -q` exits 0.

Validation: run the test command after editing; if it fails, read the failure, fix, and rerun.

Expected reply: the files changed, the test command's output pasted verbatim, and anything not done.

Stop/ask condition: if ledger.py or test_ledger.py is missing or does not contain `Entry`, report what is missing and stop.