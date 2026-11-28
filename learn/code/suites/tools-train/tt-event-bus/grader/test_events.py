import audit
from events import EventBus


def test_handlers_run_in_order_and_count_is_returned():
    bus, seen = EventBus(), []
    bus.subscribe("x", lambda p: seen.append(("a", p)))
    bus.subscribe("x", lambda p: seen.append(("b", p)))
    bus.subscribe("y", lambda p: seen.append(("c", p)))
    assert bus.publish("x", 1) == 2
    assert seen == [("a", 1), ("b", 1)]
    assert bus.publish("nobody") == 0


def test_unsubscribe_stops_delivery():
    bus, log = EventBus(), []
    handler = audit.attach(bus, log)
    bus.publish("saved", {"id": 3})
    bus.unsubscribe("saved", handler)
    bus.unsubscribe("saved", handler)
    bus.publish("saved", {"id": 4})
    assert log == ["saved 3"]


def test_unsubscribe_during_publish_skips_nobody():
    bus, seen = EventBus(), []

    def once(p):
        seen.append("once")
        bus.unsubscribe("x", once)

    bus.subscribe("x", once)
    bus.subscribe("x", lambda p: seen.append("second"))
    bus.subscribe("x", lambda p: seen.append("third"))
    assert bus.publish("x") == 3
    assert seen == ["once", "second", "third"]
    seen.clear()
    assert bus.publish("x") == 2
    assert seen == ["second", "third"]
