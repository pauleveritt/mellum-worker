Bounded task in cwd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-kmgpuii7/rung2 (repo "rung2", branch baseline).

Goal: add a `balance()` function to ledger.py that sums the entries, plus a test in test_ledger.py.

Files (current contents):
ledger.py:
---
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
---
test_ledger.py:
---
from ledger import Entry, entries_from_lines


def test_parses_lines():
    assert entries_from_lines(["coffee, -3", "pay, 10"]) == [
        Entry("coffee", -3),
        Entry("pay", 10),
    ]
---

Requirements:
1. Add `def balance(entries):` to ledger.py that returns the sum of `entry.amount` over `entries`. Accept any iterable of Entry; an empty input must return 0. Use `sum(...)` with a generator; do not mutate input.
2. Add a test in test_ledger.py: import balance and assert it sums mixed signed amounts (include a negative) and that empty input returns 0.
3. Keep existing code and style intact; minimal diff only. Use the repo's venv: run `.venv/bin/python -m pytest -q` (or `uv run pytest -q` if that fails) and make sure all tests pass.
4. Do not touch any other files, do not commit.

Report back: exact diff of both files, the pytest output, and any uncertainty.