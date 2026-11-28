"""Flag parsing."""
import enum


class _Flag(enum.Enum):
    UNKNOWN = "UNKNOWN"

    def __repr__(self):
        return "UNKNOWN"


UNKNOWN = _Flag.UNKNOWN


def parse_flag(text: str):
    word = text.strip().lower()
    if word in ("yes", "on", "1"):
        return True
    if word in ("no", "off", "0"):
        return False
    return UNKNOWN
