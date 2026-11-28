"""Order models."""
from dataclasses import dataclass, field
from decimal import Decimal

from shop.pricing import apply_discount


def to_cents(amount) -> int:
    """Convert a money amount (str, int or Decimal) to whole cents."""
    return int((Decimal(str(amount)) * 100).to_integral_value())


@dataclass
class Line:
    sku: str
    price: str
    qty: int = 1

    def cents(self) -> int:
        return to_cents(self.price) * self.qty


@dataclass
class Order:
    lines: list = field(default_factory=list)
    discount_code: str | None = None

    def total_cents(self) -> int:
        subtotal = sum(line.cents() for line in self.lines)
        return apply_discount(subtotal, self.discount_code)
