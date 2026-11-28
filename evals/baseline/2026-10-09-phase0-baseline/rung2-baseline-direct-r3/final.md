Added `balance()` function to `ledger.py` that sums the amounts of entries, and included a test for it in `test_ledger.py`. Runs pytest, and both tests passed.

Test output:
```
..                                                                       [100%]
2 passed in 0.00s
```

Files changed:
- ledger.py: Added `balance` function before `entries_from_lines`.
- test_ledger.py: Updated import to include `balance` and added `test_balance` function.