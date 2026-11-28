from decimal import Decimal

from billing.cart import line_total, subtotal
from billing.invoice import invoice, vat


def test_line_total_rounds_half_up_as_decimal():
    total = line_total("2.675", 1)
    assert isinstance(total, Decimal)
    assert total == Decimal("2.68")
    assert line_total("0.335", 3) == Decimal("1.01")


def test_vat_rounds_half_up_as_decimal():
    tax = vat(Decimal("0.70"))
    assert isinstance(tax, Decimal)
    assert tax == Decimal("0.11")


def test_invoice_adds_up_exactly():
    result = invoice([("2.675", 1), ("0.70", 1)])
    assert result["subtotal"] == Decimal("3.38")
    assert result["vat"] == Decimal("0.51")
    assert result["total"] == Decimal("3.89")
    assert all(isinstance(v, Decimal) for v in result.values())


def test_subtotal_is_decimal():
    assert subtotal([("0.10", 1), ("0.20", 1)]) == Decimal("0.30")
    assert isinstance(subtotal([("0.10", 1)]), Decimal)
