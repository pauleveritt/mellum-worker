"""HTML rendering."""
from html import escape


def html(fragment) -> str:
    return escape(str(fragment), quote=False)
