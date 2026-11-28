from metrics import Counters, Sample


def test_sample_is_closed():
    assert Sample.__closed__ is True
    assert set(Sample.__annotations__) == {"name", "value"}


def test_counters_allow_int_extras():
    assert Counters.__extra_items__ is int
    assert Counters.__required_keys__ == frozenset({"host"})
