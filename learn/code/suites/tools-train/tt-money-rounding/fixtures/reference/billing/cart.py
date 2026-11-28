"""Shopping cart totals."""
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_cents(amount) -> Decimal:
    return Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(price: str, qty: int) -> Decimal:
    """Price (a string like '2.675') times quantity, rounded to cents."""
    return to_cents(Decimal(price) * qty)


def subtotal(lines) -> Decimal:
    """lines: iterable of (price, qty)."""
    return to_cents(sum((line_total(p, q) for p, q in lines), Decimal("0")))
