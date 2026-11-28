from eventlog.events import parse


def test_parse_keeps_offset():
    event = parse("login,2026-03-01T10:00:00+02:00")
    assert event.kind == "login"
    assert event.at.utcoffset().total_seconds() == 7200
