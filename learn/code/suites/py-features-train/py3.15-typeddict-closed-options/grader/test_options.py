from options import Env, Options


def test_options_are_closed_and_optional():
    assert Options.__closed__ is True
    assert Options.__required_keys__ == frozenset()
    assert set(Options.__optional_keys__) == {"retries", "verbose"}


def test_env_allows_str_extras():
    assert Env.__extra_items__ is str
    assert Env.__required_keys__ == frozenset()
