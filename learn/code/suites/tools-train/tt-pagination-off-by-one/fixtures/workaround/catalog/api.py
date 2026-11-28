"""The functions the web layer calls."""
from catalog import paging, query, store


def list_products(page=1, per_page=10, max_price=None):
    products = query.ordered(store.all_products())
    if max_price is not None:
        products = query.cheaper_than(products, max_price)
    result = paging.paginate(products, page - 1, per_page)
    return {"page": page, "total_pages": result.total_pages,
            "items": result.items}
