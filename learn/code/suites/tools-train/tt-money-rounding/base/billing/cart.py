"""Shopping cart totals."""


def line_total(price: str, qty: int):
    """Price (a string like '2.675') times quantity, rounded to cents."""
    return round(float(price) * qty, 2)


def subtotal(lines):
    """lines: iterable of (price, qty)."""
    return round(sum(line_total(p, q) for p, q in lines), 2)
