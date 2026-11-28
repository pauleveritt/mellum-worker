"""Introspection helpers."""


def param_types(func) -> dict[str, str]:
    return {k: getattr(v, "__name__", str(v)) for k, v in func.__annotations__.items()}
