Done. `mellum-worker` (run `89b11b2b`) implemented it, and I verified the result myself.

**Final state — `ledger.py`:**
```python
def balance(entries):
    return sum(entry.amount for entry in entries)
```

**`test_ledger.py`** gained:
- `test_balance_empty` → `balance([]) == 0`
- `test_balance_sum` → `balance(entries_from_lines(["coffee, -3", "pay", 10])) == 7`

**Verification (parent, re-run after my cleanup):**
```
$ uv run pytest -q
...                                                                      [100%]
3 passed in 0.00s
```

Worker's output matched its claims; the only defect was both files missing a trailing newline, which I fixed. Nothing was committed — changes are unstaged in the worktree.