"""HTML rendering."""
from html import escape
from string.templatelib import Interpolation, Template


def html(fragment: Template) -> str:
    return "".join(escape(str(part.value)) if isinstance(part, Interpolation) else part for part in fragment)
