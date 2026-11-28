from appconf.loader import load_settings


def test_reads_file():
    settings = load_settings(env={})
    assert settings.port == 8080


def test_port_override():
    assert load_settings(env={"APP_PORT": "9000"}).port == 9000
