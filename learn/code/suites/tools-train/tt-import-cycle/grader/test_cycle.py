import subprocess
import sys


def fresh_import(module):
    return subprocess.run([sys.executable, "-c", f"import {module}"], capture_output=True, text=True)


def test_each_module_imports_on_its_own():
    for module in ("shop.models", "shop.pricing", "shop.money"):
        done = fresh_import(module)
        assert done.returncode == 0, done.stderr


def test_to_cents_lives_in_money():
    from shop.money import to_cents
    assert to_cents("19.99") == 1999
    assert to_cents(3) == 300


def test_orders_and_discounts_unchanged():
    from shop.models import Line, Order
    assert Order([Line("a", "12.50", 2)], "TEN").total_cents() == 2250
    assert Order([Line("a", "5.00", 1)], "HALF").total_cents() == 500
