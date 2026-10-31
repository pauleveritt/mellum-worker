In the current directory (a Python project) there is `ledger.py`:

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

and `test_ledger.py`:

```python
from ledger import Entry, entries_from_lines


def test_parses_lines():
    assert entries_from_lines(["coffee, -3", "pay, 10"]) == [
        Entry("coffee", -3),
        Entry("pay", 10),
    ]
```

TASK:
1. Add a function `balance(entries)` to `ledger.py` that takes an iterable/list of `Entry` objects and returns the sum of their `amount` values (an int). Return 0 for an empty list.
2. Add a test to `test_ledger.py` that verifies `balance` sums entries correctly (e.g. via `entries_from_lines(["coffee, -3", "pay, 10"])` == 7, and empty list == 0).

Use the project's virtualenv for running tests: `.venv/bin/pytest` (or `uv run pytest`). Actually run the test suite and confirm it passes before reporting.

Report exactly: the final contents of both files, the exact pytest command you ran, and its output.