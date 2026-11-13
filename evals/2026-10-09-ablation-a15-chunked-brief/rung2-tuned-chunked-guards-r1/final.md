**Files changed:**

*ledger.py*:
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

def balance(entries):
    return sum(entry.amount for entry in entries)
```

*test_ledger.py*:
```python
from ledger import Entry, entries_from_lines, balance


def test_parses_lines():
    assert entries_from_lines(["coffee, -3", "pay, 10"]) == [
        Entry("coffee", -3),
        Entry("pay", 10),
    ]


def test_balances():
    entries = entries_from_lines(["coffee, -3", "pay", 10])
    assert balance(entries) == 7


def test_balance_empty():
    assert balance([]) == 0
```

**Test output:**
```
...                                                                      [100%]
3 passed in 0.01s
```