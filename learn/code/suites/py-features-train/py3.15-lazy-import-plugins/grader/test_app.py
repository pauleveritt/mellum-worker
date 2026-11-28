import importlib
import sys


def fresh_app():
    for name in ("app", "plugins"):
        sys.modules.pop(name, None)
    return importlib.import_module("app")


def test_importing_app_does_not_load_plugins():
    app = fresh_app()
    assert "plugins" not in sys.modules
    assert "plugins" in vars(app)  # still a module-level name


def test_run_loads_plugins_on_first_use():
    app = fresh_app()
    assert app.run() == "csv, json, xml"
    assert "plugins" in sys.modules
