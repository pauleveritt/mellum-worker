"""Bulk import of stock movements."""
from dataclasses import dataclass, field

from stock.parsers import parse_record


@dataclass
class ImportResult:
    records: list = field(default_factory=list)
    errors: list = field(default_factory=list)  # 1-based line numbers of rejected lines


def import_lines(lines) -> ImportResult:
    result = ImportResult()
    for line in lines:
        if not line.strip():
            continue
        record = parse_record(line)
        if record is not None:
            result.records.append(record)
    return result
