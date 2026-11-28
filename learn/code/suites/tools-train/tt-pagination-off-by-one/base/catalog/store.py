"""In-memory product data."""

PRODUCTS = [{"id": i, "name": f"Product {i:02d}", "price": 5 + i} for i in range(1, 24)]


def all_products():
    return list(PRODUCTS)
