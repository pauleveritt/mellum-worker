"""Parse stock-movement records of the form 'SKU;QTY;WAREHOUSE'."""
from dataclasses import dataclass


@dataclass
class Record:
    sku: str
    qty: int
    warehouse: str


def parse_record(line: str):
    try:
        sku, qty, warehouse = (part.strip() for part in line.split(";"))
        qty = int(qty)
        if not sku or qty <= 0:
            raise ValueError(line)
        return Record(sku, qty, warehouse)
    except Exception:
        return None
