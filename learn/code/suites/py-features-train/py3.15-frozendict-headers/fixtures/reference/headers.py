"""HTTP header parsing."""


def parse(raw: str):
    pairs = (line.split(":", 1) for line in raw.splitlines() if line.strip())
    return frozendict((name.strip().lower(), value.strip()) for name, value in pairs)
