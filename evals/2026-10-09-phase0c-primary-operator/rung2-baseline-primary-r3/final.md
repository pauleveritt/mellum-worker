Added `balance()` function to `ledger.py` that sums the amounts of entries, and added a corresponding test `test_balance()` in `test_ledger.py`. Both changes are verified with `pytest`, which now shows 2 passed tests.

**Changes:**

- `ledger.py`: Added
  ```python
  def balance(entries):
      """Return the total balance of a list of entries."""
      return sum(e.amount for e in entries)
  ```
- `test_ledger.py`: Updated imports and added
  ```python
  def test_balance():
      entries = [
          Entry("coffee", -3),
          Entry("pay", 10)
      ]
      assert balance(entries) == 7
  ```

All tests pass:
```
test_ledger.py::test_parses_lines PASSED
test_ledger.py::test_balance PASSED
```