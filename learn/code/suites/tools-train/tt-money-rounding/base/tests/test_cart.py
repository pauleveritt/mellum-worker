from billing.cart import subtotal


def test_subtotal_of_whole_amounts():
    assert subtotal([("10.00", 2), ("5.00", 1)]) == 25
