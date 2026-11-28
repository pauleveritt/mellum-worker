"""Load the application configuration."""

import json
import sys
from pathlib import Path


def merge(base, other):
    """Return `base` updated with `other`."""
    result = dict(base)
    result.update(other)
    return result


def load_config(defaults_path, user_path=None, overrides=None):
    """Defaults, then the user file, then `overrides` (a dict), each on top of the last."""
    config = json.loads(Path(defaults_path).read_text())
    if user_path is not None:
        config = merge(config, json.loads(Path(user_path).read_text()))
    if overrides:
        config = merge(config, overrides)
    return config


if __name__ == "__main__":
    print(json.dumps(load_config(*sys.argv[1:3]), indent=2))
