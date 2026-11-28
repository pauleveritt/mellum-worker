"""Load an INI settings file into a dict."""

import configparser
import json
import sys

from schema import SCHEMA


def convert(raw, kind):
    if kind is bool:
        return raw == "true"
    if kind is int:
        return int(raw)
    if kind is list:
        return raw.split(",")
    return raw


def load(path, schema=SCHEMA):
    """Return {section: {key: value}} for the INI file at `path`, typed by `schema`."""
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    result = {}
    for section in parser.sections():
        types = schema.get(section, {})
        result[section] = {key: convert(value, types.get(key, str)) for key, value in parser[section].items()}
    return result


if __name__ == "__main__":
    print(json.dumps(load(sys.argv[1]), indent=2))
