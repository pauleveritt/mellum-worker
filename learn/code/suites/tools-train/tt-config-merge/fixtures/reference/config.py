"""Load the application configuration."""

import copy
import json
import sys
from pathlib import Path


def merge(base, other):
    """Return a new dict: `other` merged deeply onto `base`; neither input is changed."""
    result = copy.deepcopy(base)
    for key, value in other.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_config(defaults_path, user_path=None, overrides=None):
    """Defaults, then the user file, then `overrides` (a dict), each on top of the last."""
    config = json.loads(Path(defaults_path).read_text())
    if user_path is not None and Path(user_path).exists():
        config = merge(config, json.loads(Path(user_path).read_text()))
    if overrides:
        config = merge(config, overrides)
    return config


if __name__ == "__main__":
    print(json.dumps(load_config(*sys.argv[1:3]), indent=2))
