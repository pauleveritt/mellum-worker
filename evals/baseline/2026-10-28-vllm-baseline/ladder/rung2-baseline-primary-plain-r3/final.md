Added a `balance()` function to `ledger.py` that sums the amounts of a list of `Entry` objects, and included a test for it in `test_ledger.py`. Both tests now pass:

```bash
$ python -m pytest test_ledger.py
..
============================== 2 passed in 0.00s ===============================
```

The changes are ready.