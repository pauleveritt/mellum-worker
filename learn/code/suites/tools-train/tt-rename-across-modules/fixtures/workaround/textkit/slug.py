"""URL slugs."""
import re

from textkit.normalize import normalize_text


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", normalize_text(title)).strip("-")
