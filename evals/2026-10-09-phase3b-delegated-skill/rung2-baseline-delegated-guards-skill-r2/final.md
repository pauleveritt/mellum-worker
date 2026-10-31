Done. mellum-worker implemented it, and I independently verified (plus fixed two lint nits it left behind).

**`ledger.py`** — added:
```python
def balance(entries):
    return sum(e.amount for e in entries)
```

**`test_ledger.py`** — added:
```python
def test_balance():
    assert balance([]) == 0
    assert balance([Entry("coffee", -3), Entry("pay", 10)]) == 7
```

Verification (run by me, in the repo):
- `uv run pytest -q` → `2 passed`
- `uv run ruff check .` → clean

Cleanups applied after the subagent: added the missing trailing newlines to both files and let ruff sort the import (`Entry, balance, entries_from_lines`). No other behavior changed.