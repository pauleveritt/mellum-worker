from datetime import date

from invoicing.billing import due_date, is_overdue
from invoicing.format import money


def test_net3_from_a_thursday_skips_the_weekend():
    assert due_date(date(2026, 1, 8), "net3") == date(2026, 1, 13)


def test_not_overdue_on_the_due_date():
    assert not is_overdue(date(2026, 1, 8), "net3", date(2026, 1, 13))


def test_money():
    assert money(123456) == "R1,234.56"
