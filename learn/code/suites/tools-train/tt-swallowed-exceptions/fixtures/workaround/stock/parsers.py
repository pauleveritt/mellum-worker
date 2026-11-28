"""Parse stock-movement records of the form 'SKU;QTY;WAREHOUSE'."""
from dataclasses import dataclass


class RecordError(ValueError):
    """A line that is not a valid stock-movement record."""


@dataclass
class Record:
    sku: str
    qty: int
    warehouse: str


def parse_record(line: str) -> Record:
    parts = [part.strip() for part in line.split(";")]
    if len(parts) != 3:
        raise RecordError(f"expected 3 fields, got {len(parts)}: {line!r}")
    sku, qty, warehouse = parts
    if not sku:
        raise RecordError(f"missing SKU: {line!r}")
    try:
        qty = int(qty)
    except ValueError:
        raise RecordError(f"quantity is not a number: {line!r}") from None
    if qty <= 0:
        raise RecordError(f"quantity must be positive: {line!r}")
    return Record(sku, qty, warehouse)
