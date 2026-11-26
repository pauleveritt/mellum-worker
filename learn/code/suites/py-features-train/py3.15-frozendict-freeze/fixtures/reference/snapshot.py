"""State snapshots."""


def freeze(value):
    if isinstance(value, dict):
        return frozendict((k, freeze(v)) for k, v in value.items())
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    return value
