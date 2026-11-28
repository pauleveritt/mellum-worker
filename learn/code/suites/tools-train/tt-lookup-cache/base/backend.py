"""A slow price backend. Every call is a round trip, so callers should not repeat them."""
import time

PRICES = {"A": 10, "B": 25, "C": 7, "D": 99}
CALLS = []


def query(sku):
    CALLS.append(sku)
    time.sleep(0.01)
    return PRICES[sku]
