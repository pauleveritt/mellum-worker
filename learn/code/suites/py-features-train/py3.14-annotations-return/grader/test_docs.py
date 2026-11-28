from docs import return_text


def orders() -> Iterator[Order]:  # noqa: F821 - never defined
    return iter([])


def test_undefined_return_is_described_not_evaluated():
    assert return_text(orders) == "Iterator[Order]"


def test_unannotated_return_is_none():
    def ping(host: str):
        return None
    assert return_text(ping) is None
