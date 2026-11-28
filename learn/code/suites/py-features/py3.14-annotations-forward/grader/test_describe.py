from schema import describe


class Ticket:
    owner: User  # noqa: F821 - User is never defined
    tags: list[str]
    count: int


def test_undefined_names_are_described_not_evaluated():
    assert describe(Ticket) == {"owner": "User", "tags": "list[str]", "count": "int"}


def test_plain_class():
    class Point:
        x: float
        y: float
    assert describe(Point) == {"x": "float", "y": "float"}
