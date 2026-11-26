from flags import UNKNOWN, parse_flag


def test_unknown_is_a_builtin_sentinel():
    assert repr(UNKNOWN) == "UNKNOWN"
    assert type(UNKNOWN) is type(sentinel("OTHER"))  # noqa: F821 - a builtin on this Python


def test_parse_flag():
    assert parse_flag(" Yes ") is True and parse_flag("0") is False
    assert parse_flag("maybe") is UNKNOWN
