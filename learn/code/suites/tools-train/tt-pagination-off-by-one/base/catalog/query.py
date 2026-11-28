"""Filtering and ordering of products."""


def ordered(products, key="id"):
    return sorted(products, key=lambda p: p[key])


def cheaper_than(products, limit):
    return [p for p in products if p["price"] < limit]
