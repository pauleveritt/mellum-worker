"""Bulk import of stock movements."""
from dataclasses import dataclass, field

from stock.parsers import RecordError, parse_record


@dataclass
class ImportResult:
    records: list = field(default_factory=list)
    errors: list = field(default_factory=list)  # 1-based line numbers of rejected lines


def import_lines(lines) -> ImportResult:
    result = ImportResult()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            result.records.append(parse_record(line))
        except RecordError:
            result.errors.append(number)
    return result
