"""Clean a CSV export of customer records."""

import csv
import sys
from datetime import datetime


def dedupe(in_path, out_path, key="id", stamp="updated_at"):
    """Write `in_path` to `out_path` with one row per `key`, keeping the row with the newest `stamp`."""
    with open(in_path, newline="", encoding="utf-8") as src:
        reader = csv.DictReader(src)
        fields = reader.fieldnames
        best = {}
        for row in reader:
            current = best.get(row[key])
            if current is None or datetime.fromisoformat(row[stamp]) > datetime.fromisoformat(current[stamp]):
                best[row[key]] = row
    with open(out_path, "w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=fields)
        writer.writeheader()
        writer.writerows(best.values())


if __name__ == "__main__":
    dedupe(sys.argv[1], sys.argv[2])
