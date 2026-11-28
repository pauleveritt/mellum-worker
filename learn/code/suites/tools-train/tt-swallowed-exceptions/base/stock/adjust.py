"""Single manual adjustments typed in by staff."""
from stock.parsers import parse_record


def adjustment(line: str):
    record = parse_record(line)
    return {"sku": record.sku, "delta": record.qty, "warehouse": record.warehouse}
