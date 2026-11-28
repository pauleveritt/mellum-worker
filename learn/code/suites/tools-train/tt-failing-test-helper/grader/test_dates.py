from datetime import date

from invoicing.billing import due_date
from invoicing.dates import add_business_days, is_business_day


def test_saturday_and_sunday_are_not_business_days():
    assert not is_business_day(date(2026, 1, 10))
    assert not is_business_day(date(2026, 1, 11))
    assert is_business_day(date(2026, 1, 12))


def test_one_business_day_after_friday_is_monday():
    assert add_business_days(date(2026, 1, 9), 1) == date(2026, 1, 12)


def test_due_dates():
    assert due_date(date(2026, 1, 8), "net3") == date(2026, 1, 13)
    assert due_date(date(2026, 1, 5), "net10") == date(2026, 1, 19)
