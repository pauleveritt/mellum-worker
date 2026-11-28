"""Invoices: subtotal, VAT and total."""
from decimal import ROUND_HALF_UP, Decimal

from billing.cart import subtotal

VAT_RATE = "0.15"


def vat(amount, rate=VAT_RATE):
    return Decimal(float(amount) * float(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def invoice(lines, rate=VAT_RATE) -> dict:
    net = subtotal(lines)
    tax = vat(net, rate)
    return {"subtotal": net, "vat": tax, "total": round(float(net) + float(tax), 2)}
