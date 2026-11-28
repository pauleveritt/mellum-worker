"""textkit: small text utilities."""
from textkit.normalize import normalize_text
from textkit.search import matches, search
from textkit.slug import slugify
from textkit.tags import unique_tags

__all__ = ["normalize_text", "matches", "search", "slugify", "unique_tags"]
