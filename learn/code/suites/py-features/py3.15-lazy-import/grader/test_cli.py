import importlib
import sys


def fresh_cli():
    for name in ("cli", "reports"):
        sys.modules.pop(name, None)
    return importlib.import_module("cli")


def test_importing_cli_does_not_load_reports():
    cli = fresh_cli()
    assert "reports" not in sys.modules
    assert "reports" in vars(cli)  # still a module-level name


def test_main_loads_reports_on_first_use():
    cli = fresh_cli()
    assert cli.main() == "3 reports"
    assert "reports" in sys.modules
