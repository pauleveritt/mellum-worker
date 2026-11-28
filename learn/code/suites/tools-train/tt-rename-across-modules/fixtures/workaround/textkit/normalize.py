"""Text normalisation."""
import re
import unicodedata


def normalize_text(text):
    """Lower-case, strip accents and collapse runs of whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()
