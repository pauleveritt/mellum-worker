"""Database helpers."""
from string.templatelib import Interpolation, Template


def sql(query: Template) -> tuple[str, list]:
    text, params = [], []
    for part in query:
        if isinstance(part, Interpolation):
            text.append("?")
            params.append(part.value)
        else:
            text.append(part)
    return "".join(text), params
