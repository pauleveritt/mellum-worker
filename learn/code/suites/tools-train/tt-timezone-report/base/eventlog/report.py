"""Daily reports."""
from collections import Counter
from datetime import date

from eventlog.window import day_bounds


def events_on(events, day: date):
    start, end = day_bounds(day)
    return [e for e in events if start <= e.at < end]


def daily_summary(events, day: date) -> dict:
    return dict(Counter(e.kind for e in events_on(events, day)))
