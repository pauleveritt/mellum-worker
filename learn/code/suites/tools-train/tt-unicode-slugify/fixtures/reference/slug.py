"""Slugs for URLs and file names."""
import re
import unicodedata


def slugify(text):
    """'Crème Brûlée!' -> 'creme-brulee'."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
