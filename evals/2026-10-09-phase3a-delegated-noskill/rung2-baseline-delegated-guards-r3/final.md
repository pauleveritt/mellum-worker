Done and verified independently.

**Changes**
- `ledger.py` — added:
  ```python
  def balance(entries):
      total = 0
      for entry in entries:
          total += entry.amount
      return total
  ```
  Sums `entry.amount` over any iterable; returns `0` for an empty iterable.
- `test_ledger.py` — added `test_balance` (`-3 + 10 == 7`), importing `balance`.

**Evidence** (run by me, not just the child)
```
$ .venv/bin/pytest -q
..                                                       [100%]
2 passed in 0.00s
exit=0
```
`git status --short`: only `ledger.py` and `test_ledger.py` modified (`.pi/` is pre-existing untracked). No other files touched.

Note: the empty-ledger case returns 0 but has no dedicated test — the task specified exactly one new test, so I left it as-is. Say the word if you want that case covered too.