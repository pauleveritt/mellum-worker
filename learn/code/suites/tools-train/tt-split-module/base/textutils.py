"""Text helpers for reports."""
from datetime import date

def title_case(text):
    """Capitalise each word, keeping short joining words lower case (except the first)."""
    small = {"a", "an", "and", "of", "the", "to"}
    words = text.lower().split()
    return " ".join(w if i and w in small else w.capitalize() for i, w in enumerate(words))


def truncate(text, width, marker="..."):
    if len(text) <= width:
        return text
    return text[: max(width - len(marker), 0)] + marker


def word_count(text):
    return len(text.split())

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
