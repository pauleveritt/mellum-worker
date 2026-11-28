"""Invoice terms."""
from datetime import date

from invoicing.dates import add_business_days

TERMS = {"net3": 3, "net5": 5, "net10": 10}


def due_date(issued: date, terms: str) -> date:
    return add_business_days(issued, TERMS[terms])


def is_overdue(issued: date, terms: str, today: date) -> bool:
    return today > due_date(issued, terms)
