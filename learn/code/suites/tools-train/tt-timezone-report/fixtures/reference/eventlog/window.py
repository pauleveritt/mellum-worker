"""Time windows used by reports."""
from datetime import UTC, date, datetime, time, timedelta


def day_bounds(day: date):
    """Start (inclusive) and end (exclusive) of a UTC calendar day, as aware datetimes."""
    start = datetime.combine(day, time.min, tzinfo=UTC)
    return start, start + timedelta(days=1)
