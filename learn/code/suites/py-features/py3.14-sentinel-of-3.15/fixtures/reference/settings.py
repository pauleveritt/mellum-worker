"""Settings lookup."""


class _Missing:
    def __repr__(self):
        return "MISSING"


MISSING = _Missing()


def lookup(mapping, key, default=MISSING):
    if key in mapping:
        return mapping[key]
    if default is MISSING:
        raise KeyError(key)
    return default
