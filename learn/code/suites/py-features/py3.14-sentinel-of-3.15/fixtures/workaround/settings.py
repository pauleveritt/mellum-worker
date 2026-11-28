"""Settings lookup."""

MISSING = sentinel("MISSING")


def lookup(mapping, key, default=MISSING):
    if key in mapping:
        return mapping[key]
    if default is MISSING:
        raise KeyError(key)
    return default
