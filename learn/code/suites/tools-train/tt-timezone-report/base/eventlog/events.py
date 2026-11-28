"""Event records."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    kind: str
    at: datetime


def parse(line: str) -> Event:
    """Parse 'kind,ISO-8601 timestamp with offset'."""
    kind, stamp = line.strip().split(",", 1)
    return Event(kind, datetime.fromisoformat(stamp))
