"""Discounts and price rules."""

CODES = {"TEN": 10, "HALF": 50}
MINIMUM_SPEND = "20.00"


def apply_discount(subtotal_cents: int, code: str | None) -> int:
    from shop.models import to_cents

    if code not in CODES or subtotal_cents < to_cents(MINIMUM_SPEND):
        return subtotal_cents
    return subtotal_cents - subtotal_cents * CODES[code] // 100
