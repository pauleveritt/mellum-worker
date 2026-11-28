"""Builds the one-line project summary."""
from textutils import days_between, format_date, parse_date, title_case, truncate


def summary(name, start, end):
    span = days_between(start, end)
    when = f"{format_date(parse_date(start))} to {format_date(parse_date(end))}"
    return truncate(f"{title_case(name)}: {when} ({span} days)", 60)
