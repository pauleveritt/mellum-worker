"""Config loading."""
from collections.abc import Mapping


class FrozenConfig(Mapping):
    def __init__(self, pairs):
        self._data = dict(pairs)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __hash__(self):
        return hash(frozenset(self._data.items()))


def load(text: str) -> FrozenConfig:
    pairs = (line.split("=", 1) for line in text.splitlines() if line.strip() and not line.startswith("#"))
    return FrozenConfig((key.strip(), value.strip()) for key, value in pairs)
