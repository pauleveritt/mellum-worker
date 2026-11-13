Done — delegated to **mellum-worker** (project agent, `omlx/Mellum2.1-12B-A2.5B-Thinking-6bit`), then verified independently.

**Changes** (uncommitted, working tree):
- `ledger.py`: added
  ```python
  def balance(entries):
      return sum(entry.amount for entry in entries)
  ```
  Empty input → `0`; works for any iterable; does not mutate input.
- `test_ledger.py`: added `test_balance` asserting `balance([Entry("coffee", -3), Entry("pay", 10)]) == 7` and `balance([]) == 0`, importing `balance`.

**Verification** (run by me, not just reported): `.venv/bin/python -m pytest -q` → `2 passed in 0.00s`.

One small correction I made on top of the worker's diff: it left only one blank line before `balance()`; I restored the file's PEP8/two-blank-line style. No other files touched, nothing committed.