"""Load an INI settings file into a dict."""

import configparser
import json
import sys

from schema import SCHEMA


TRUE = {"true", "yes", "on", "1"}
FALSE = {"false", "no", "off", "0"}


def convert(raw, kind):
    if kind is bool:
        word = raw.strip().lower()
        if word in TRUE:
            return True
        if word in FALSE:
            return False
        raise ValueError(f"not a boolean: {raw!r}")
    if kind is int:
        return int(raw)
    if kind is list:
        return [item.strip() for item in raw.split(",") if item.strip()]
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
