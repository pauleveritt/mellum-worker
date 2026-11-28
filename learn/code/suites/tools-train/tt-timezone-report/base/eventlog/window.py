"""Time windows used by reports."""
from datetime import date, datetime, time, timedelta


def day_bounds(day: date):
    """Start (inclusive) and end (exclusive) of a calendar day."""
    start = datetime.combine(day, time.min)
    return start, start + timedelta(days=1)
