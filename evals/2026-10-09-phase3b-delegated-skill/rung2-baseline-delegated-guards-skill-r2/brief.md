Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-usss9dhi/rung2

Task: Add a `balance()` function to ledger.py that sums an iterable of Entry objects and returns the total of their `amount` fields as an int. Then add a pytest test for it.

Context (existing files, do not restructure):
ledger.py currently is:
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    memo: str
    amount: int


def entries_from_lines(lines):
    out = []
    for line in lines:
        memo, amount = line.rsplit(",", 1)
        out.append(Entry(memo.strip(), int(amount)))
    return out
```

test_ledger.py imports `from ledger import Entry, entries_from_lines`.

Requirements:
- Add `def balance(entries):` in ledger.py that returns `sum(e.amount for e in entries)`. An empty iterable must return 0.
- Add a test to test_ledger.py named `test_balance` that builds Entries (e.g. Entry("coffee", -3), Entry("pay", 10)) and asserts the sum; also cover the empty case.
- Match existing style (plain functions, no new deps).
- Run the tests with `uv run pytest -q` (fall back to `.venv/bin/pytest -q` if uv is unavailable) and report the exact command and result.
- Make ONLY these two edits. Do not change other behavior.

Report back: files changed, the exact test command, and its output.