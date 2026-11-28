"""Documentation helpers."""


def return_text(func):
    value = func.__annotations__.get("return")
    return None if value is None else getattr(value, "__name__", str(value))
