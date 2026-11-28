Verified the rename operation:

1. **Search for remaining occurrences:**  
   `grep -R "fetch_rows" . --exclude-dir=.venv` produced no output, confirming the function name has been replaced everywhere.

2. **Run verification test:**  
   `python test_report.py`  
   Exit code: 0  
   Output: (empty, indicating all tests pass)

3. **Check file contents:**  
   - `rows.py` now contains `def load_rows(source):`  
   - `report.py` contains `from rows import load_rows` and `load_rows(source)`

✅ **Verification successful:** The rename from `fetch_rows` to `load_rows` has been completed and verified across the codebase.