from catalog import query, store


def test_ordered_by_id():
    ids = [p["id"] for p in query.ordered(store.all_products())]
    assert ids == sorted(ids)
