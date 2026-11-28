"""URL slugs."""
import re

from textkit.normalize import clean


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", clean(title)).strip("-")
