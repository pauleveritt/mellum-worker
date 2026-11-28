from appconf.loader import load_settings


def test_file_timeout_used_without_override():
    settings = load_settings(env={})
    assert settings.timeout == 30.0
    assert isinstance(settings.timeout, float)


def test_timeout_override_applies_as_a_float():
    settings = load_settings(env={"APP_TIMEOUT": "2.5"})
    assert settings.timeout == 2.5
    assert isinstance(settings.timeout, float)


def test_other_overrides_still_work_alongside():
    settings = load_settings(env={"APP_TIMEOUT": "7", "APP_HOST": "0.0.0.0"})
    assert settings.host == "0.0.0.0"
    assert settings.timeout == 7.0
    assert settings.port == 8080
