Done, via mellum-worker, and independently verified.

**Result** — `balance(entries)` in `ledger.py` sums `Entry.amount`; test added in `test_ledger.py`:

```python
def balance(entries):
    return sum(e.amount for e in entries)
```

**Verification (parent, not child):**
```
$ uv run --offline pytest -q
2 passed in 0.00s
```

Minor nit: both files now end without a trailing newline (`\ No newline at end of file` in the diff). Want me to add them?