"""Clean a CSV export of customer records."""

import csv
import sys


def dedupe(in_path, out_path, key="id", stamp="updated_at"):
    """Write `in_path` to `out_path` with one row per `key`. TODO: not implemented yet."""
    with open(in_path, newline="", encoding="utf-8") as src:
        rows = list(csv.DictReader(src))
    raise NotImplementedError(f"{len(rows)} rows read; deduplication not written yet")


if __name__ == "__main__":
    dedupe(sys.argv[1], sys.argv[2])
