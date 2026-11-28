"""Money helpers shared across the shop."""
from decimal import Decimal


def to_cents(amount) -> int:
    """Convert a money amount (str, int or Decimal) to whole cents."""
    return int((Decimal(str(amount)) * 100).to_integral_value())
