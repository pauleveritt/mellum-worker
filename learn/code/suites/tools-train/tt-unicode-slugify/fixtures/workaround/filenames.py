"""Turn document titles into safe file names."""
from slug import slugify


def safe_filename(title, ext="txt"):
    return f"{slugify(title)}.{ext}"
