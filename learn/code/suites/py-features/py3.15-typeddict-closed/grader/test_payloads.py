from payloads import Event, Labels


def test_event_is_closed():
    assert Event.__closed__ is True
    assert set(Event.__annotations__) == {"name", "at"}


def test_labels_allow_str_extras():
    assert Labels.__extra_items__ is str
    assert Labels.__required_keys__ == frozenset({"id"})
