"""Schema helpers."""


def describe(cls) -> dict[str, str]:
    return {name: getattr(value, "__name__", str(value)) for name, value in cls.__annotations__.items()}
