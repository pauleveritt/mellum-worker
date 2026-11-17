Done. Delegated the task to `mellum-worker` (run `c8c0a045`), then independently re-ran the suite myself to confirm.

**Files changed**
- `ledger.py` — added:
  ```python
  def balance(entries):
      return sum(entry.amount for entry in entries)
  ```
- `test_ledger.py` — added `test_balance_single`, `test_balance_with_negative`, `test_balance_empty`

**Verification (parent-run, not just the child's claim)**
```
$ uv run --offline pytest -q
....                                                                     [100%]
4 passed in 0.00s
exit=0
```

Notes:
- The worker's own loop caught and fixed a bug: its first test passed a bare `Entry` instead of a list, which failed (`'Entry' object is not iterable`), then it corrected the test and passed. The final signature accepts an iterable of entries.
- I added the missing trailing newlines at EOF in both files (cosmetic; no content change).