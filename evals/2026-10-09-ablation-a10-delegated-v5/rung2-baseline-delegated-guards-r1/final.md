Done. `mellum-worker` implemented it, and I verified the files and test run directly.

**`ledger.py`** — added:
```python
def balance(entries):
    return sum(entry.amount for entry in entries)
```

**`test_ledger.py`** — added `test_balance`, covering `["coffee, -3", "pay, 10"] → 7` and empty list `→ 0`.

Verification (run by me, not just the worker's report):
```
$ .venv/bin/pytest -q
2 passed in 0.00s
```

Note: `balance([])` returning `0` is inherent to `sum(..., 0)` since the generator yields nothing.