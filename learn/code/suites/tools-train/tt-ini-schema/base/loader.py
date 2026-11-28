"""Load an INI settings file into a dict."""

import configparser
import json
import sys

from schema import SCHEMA


def load(path, schema=SCHEMA):
    """Return {section: {key: value}} for the INI file at `path`."""
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    return {section: dict(parser[section]) for section in parser.sections()}


if __name__ == "__main__":
    print(json.dumps(load(sys.argv[1]), indent=2))
