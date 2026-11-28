"""textkit: small text utilities."""
from textkit.normalize import clean
from textkit.search import matches, search
from textkit.slug import slugify
from textkit.tags import unique_tags

__all__ = ["clean", "matches", "search", "slugify", "unique_tags"]
