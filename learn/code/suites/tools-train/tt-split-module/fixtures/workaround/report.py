"""Builds the one-line project summary."""
from dates import days_between, format_date, parse_date
from textutils import title_case, truncate


def summary(name, start, end):
    span = days_between(start, end)
    when = f"{format_date(parse_date(start))} to {format_date(parse_date(end))}"
    return truncate(f"{title_case(name)}: {when} ({span} days)", 60)
