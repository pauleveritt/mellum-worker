"""Text helpers for reports."""
from dates import MONTHS, days_between, format_date, parse_date  # noqa: F401  (old import path)


def title_case(text):
    """Capitalise each word, keeping short joining words lower case (except the first)."""
    small = {"a", "an", "and", "of", "the", "to"}
    words = text.lower().split()
    return " ".join(w if i and w in small else w.capitalize() for i, w in enumerate(words))


def truncate(text, width, marker="..."):
    if len(text) <= width:
        return text
    return text[: max(width - len(marker), 0)] + marker


def word_count(text):
    return len(text.split())
