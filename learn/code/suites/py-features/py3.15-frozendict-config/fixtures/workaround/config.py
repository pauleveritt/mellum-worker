"""Config loading."""
from types import MappingProxyType


def load(text: str):
    pairs = (line.split("=", 1) for line in text.splitlines() if line.strip() and not line.startswith("#"))
    return MappingProxyType({key.strip(): value.strip() for key, value in pairs})
