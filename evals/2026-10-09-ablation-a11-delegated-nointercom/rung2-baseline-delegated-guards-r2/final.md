`mellum-worker` completed the task, and I verified it independently.

**Changes**
- `ledger.py`: added `balance(entries)` → `sum(entry.amount for entry in entries)` (empty list → `0`); existing code untouched.
- `test_ledger.py`: added `test_balance` covering `[Entry("coffee", -3), Entry("pay", 10)] == 7` and `balance([]) == 0`.

**Verification** — I re-ran the suite myself after a trailing-newline cleanup:
```
$ uv run pytest
test_ledger.py ..   [100%]
2 passed in 0.01s
```

No deviations from the requested scope; only the two files changed.