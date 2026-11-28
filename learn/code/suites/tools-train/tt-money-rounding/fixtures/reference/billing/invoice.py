"""Invoices: subtotal, VAT and total."""
from decimal import Decimal

from billing.cart import subtotal, to_cents

VAT_RATE = "0.15"


def vat(amount, rate=VAT_RATE) -> Decimal:
    return to_cents(Decimal(str(amount)) * Decimal(str(rate)))


def invoice(lines, rate=VAT_RATE) -> dict:
    net = subtotal(lines)
    tax = vat(net, rate)
    return {"subtotal": net, "vat": tax, "total": net + tax}
