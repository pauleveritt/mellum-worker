"""Invoice terms."""
from datetime import date, timedelta

from invoicing.dates import add_business_days

TERMS = {"net3": 3, "net5": 5, "net10": 10}


def due_date(issued: date, terms: str) -> date:
    due = add_business_days(issued, TERMS[terms])
    if due.weekday() == 0 and terms == "net3":
        due += timedelta(days=1)
    while due.weekday() >= 5:
        due += timedelta(days=1)
    return due


def is_overdue(issued: date, terms: str, today: date) -> bool:
    return today > due_date(issued, terms)
