"""Contact records."""


class _Unset:
    def __repr__(self):
        return "UNSET"


UNSET = _Unset()


def update(record: dict, *, email=UNSET, phone=UNSET) -> dict:
    out = dict(record)
    for key, value in (("email", email), ("phone", phone)):
        if value is not UNSET:
            out[key] = value
    return out
