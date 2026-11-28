from datetime import date

from eventlog.events import parse
from eventlog.report import daily_summary

LINES = [
    "login,2026-03-01T08:00:00+00:00",
    "login,2026-03-01T23:30:00-02:00",
    "logout,2026-03-02T01:00:00+02:00",
    "login,2026-03-02T12:00:00+00:00",
]


def events():
    return [parse(line) for line in LINES]


def test_summary_for_a_utc_day():
    assert daily_summary(events(), date(2026, 3, 2)) == {"login": 2}


def test_offset_event_lands_on_its_utc_day():
    assert daily_summary(events(), date(2026, 3, 1)) == {"login": 1, "logout": 1}


def test_empty_day():
    assert daily_summary(events(), date(2026, 3, 5)) == {}
