from catalog.api import list_products


def ids(result):
    return [p["id"] for p in result["items"]]


def test_first_page_starts_at_the_first_product():
    assert ids(list_products(page=1, per_page=10)) == list(range(1, 11))


def test_last_partial_page_is_counted_and_filled():
    first = list_products(page=1, per_page=10)
    assert first["total_pages"] == 3
    assert ids(list_products(page=3, per_page=10)) == [21, 22, 23]


def test_every_product_appears_exactly_once():
    seen = []
    total = list_products(page=1, per_page=4)["total_pages"]
    for n in range(1, total + 1):
        seen += ids(list_products(page=n, per_page=4))
    assert seen == list(range(1, 24))


def test_exact_multiple_has_no_empty_trailing_page():
    result = list_products(page=1, per_page=5, max_price=26)
    assert result["total_pages"] == 4
    assert ids(list_products(page=4, per_page=5, max_price=26)) == list(range(16, 21))
