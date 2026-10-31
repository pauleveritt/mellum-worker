Done. Delegated to `mellum-worker`, then verified the workspace directly (its final report came back empty).

**Changes** (`ledger.py`, `test_ledger.py`):
- `balance(entries)` sums `entry.amount` over the entries.
- New `test_balance_sums_amounts` covering a mixed credit/debit case (`-3 + 10 + -4 == 3`).

**Verification** (`uv run pytest -q`):
```
2 passed in 0.00s
```

Notes:
- The worker's edit was correct, but its report text was empty, so I re-ran the tests and inspected the diff myself rather than trusting an unverified summary.
- I applied two trivial cleanup fixes the worker missed: a second blank line before `balance` (PEP 8) and a trailing newline in the test file.
- The test intent was assumed (`balance` takes an iterable of `Entry` and returns the amount sum). If you meant a `Ledger` object method or a different signature, say so and I'll adjust.