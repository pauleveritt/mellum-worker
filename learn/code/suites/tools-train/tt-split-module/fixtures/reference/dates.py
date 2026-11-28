"""Date helpers for reports."""
from datetime import date

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def parse_date(text):
    """Parse 'YYYY-MM-DD' into a date."""
    year, month, day = (int(part) for part in text.strip().split("-"))
    return date(year, month, day)


def format_date(value):
    """'2024-03-05' -> '5 Mar 2024'."""
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def days_between(start, end):
    """Whole days from start to end; both are 'YYYY-MM-DD' strings."""
    return (parse_date(end) - parse_date(start)).days
