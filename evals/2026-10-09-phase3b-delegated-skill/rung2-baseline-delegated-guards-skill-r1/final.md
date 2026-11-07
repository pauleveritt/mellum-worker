Done. mellum-worker made the change; I verified it myself.

**Files changed**
- `ledger.py` — added:
  ```python
  def balance(entries):
      return sum(entry.amount for entry in entries)
  ```
- `test_ledger.py` — added `test_balance` (entries `["coffee, -3", "pay, 10"]` → `7`) and updated the import.

**Verification** (parent-run, from repo root): `uv run --offline pytest -q` → `2 passed in 0.00s` (baseline was `1 passed`).

`Entry`, `entries_from_lines`, `test_parses_lines`, and `pyproject.toml` are unchanged. Final change was the worker's — no fallback edit needed.