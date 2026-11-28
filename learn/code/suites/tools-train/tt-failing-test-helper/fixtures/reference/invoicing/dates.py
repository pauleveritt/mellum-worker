"""Calendar helpers."""
from datetime import date, timedelta


def is_business_day(day: date) -> bool:
    return day.weekday() < 5


def add_business_days(start: date, days: int) -> date:
    """The date `days` business days (Mon-Fri) after `start`."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if is_business_day(current):
            added += 1
    return current
