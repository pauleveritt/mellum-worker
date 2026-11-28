"""Order models."""
from dataclasses import dataclass, field

from shop.money import to_cents
from shop.pricing import apply_discount


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
