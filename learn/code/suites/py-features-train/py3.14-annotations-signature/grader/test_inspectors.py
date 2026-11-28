from inspectors import param_types


def fetch(user: Account, limit: int = 10) -> list[Row]:  # noqa: F821 - never defined
    return []


def test_undefined_names_are_described_not_evaluated():
    assert param_types(fetch) == {"user": "Account", "limit": "int", "return": "list[Row]"}


def test_unannotated_parameters_are_left_out():
    def ping(host, port: int):
        return None
    assert param_types(ping) == {"port": "int"}
