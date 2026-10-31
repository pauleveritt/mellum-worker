Renamed fetch_rows to load_rows in rows.py and report.py. No other files contain the identifier.

Changes made:
- rows.py: def fetch_rows(source) → def load_rows(source)
- report.py: from rows import fetch_rows → from rows import load_rows
- report.py: fetch_rows(source) → load_rows(source)

All instances updated successfully.