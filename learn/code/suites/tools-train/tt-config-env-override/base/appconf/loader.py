"""Load settings from the INI file, then apply environment overrides."""
import configparser
import os
from pathlib import Path

from appconf.env import apply_overrides
from appconf.settings import Settings

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "app.ini"


def load_settings(path=DEFAULT_PATH, env=None) -> Settings:
    parser = configparser.ConfigParser()
    parser.read(path)
    settings = Settings(
        host=parser.get("server", "host"),
        port=parser.getint("server", "port"),
        db_path=parser.get("database", "path"),
        timeout=parser.getfloat("database", "timeout"),
    )
    return apply_overrides(settings, os.environ if env is None else env)
