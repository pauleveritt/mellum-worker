"""Price lookups for the shop."""
import backend
from cache import cached


@cached(maxsize=256)
def fetch_price(sku):
    return backend.query(sku)


def basket_total(skus):
    return sum(fetch_price(sku) for sku in skus)
