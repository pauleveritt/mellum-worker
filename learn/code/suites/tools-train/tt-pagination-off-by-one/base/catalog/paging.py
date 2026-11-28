"""Split a sequence into numbered pages."""
from dataclasses import dataclass


@dataclass
class Page:
    items: list
    number: int
    total_pages: int


def page_count(total, per_page):
    return total // per_page


def slice_page(items, number, per_page):
    """Page `number` (1-based) of `items`."""
    start = number * per_page
    return list(items[start:start + per_page])


def paginate(items, number, per_page):
    items = list(items)
    return Page(slice_page(items, number, per_page), number, page_count(len(items), per_page))
