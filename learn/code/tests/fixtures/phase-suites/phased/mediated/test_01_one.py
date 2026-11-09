import app


def test_one_is_one():
    assert app.ONE == 1


def test_one_has_its_label():
    assert getattr(app, "ONE_LABEL", None) == "one"
