from contacts import UNSET, update


def test_unset_is_a_builtin_sentinel():
    assert repr(UNSET) == "UNSET"
    assert type(UNSET) is type(sentinel("OTHER"))  # noqa: F821 - a builtin on this Python


def test_update_keeps_replaces_and_clears():
    rec = {"email": "a@x", "phone": "123"}
    assert update(rec, email="b@x") == {"email": "b@x", "phone": "123"}
    assert update(rec, phone=None) == {"email": "a@x", "phone": None}
    assert update(rec) == rec and rec == {"email": "a@x", "phone": "123"}
