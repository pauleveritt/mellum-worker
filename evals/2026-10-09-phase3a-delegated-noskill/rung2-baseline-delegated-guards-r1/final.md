Done — `mellum-worker` implemented it; I verified independently.

**Changes** (`git status`: only these two files modified, nothing committed):

`ledger.py`
```python
def balance(entries):
    return sum(entry.amount for entry in entries)
```

`test_ledger.py` — import now includes `balance`, plus:
```python
def test_balance_sums_entries():
    entries = entries_from_lines(["coffee, -3", "pay, 10"])
    assert balance(entries) == 7
    assert balance([]) == 0
```

**Verification I ran myself:** `uv run pytest -q` → `2 passed in 0.00s` (both tests green, empty input returns 0).

Minor (not fixed): PEP 8 wants two blank lines between top-level functions in both files. Say the word if you want that cleaned up.