from shop.models import Line, Order


def test_total_without_discount():
    assert Order([Line("a", "4.50", 2)]).total_cents() == 900
