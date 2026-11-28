"""Load a ServerConfig from a JSON file."""
import json

from config import ServerConfig


def load(path):
    with open(path, encoding="utf-8") as fh:
        return ServerConfig.from_dict(json.load(fh))
