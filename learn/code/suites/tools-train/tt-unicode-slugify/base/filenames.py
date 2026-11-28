"""Turn document titles into safe file names."""
import re


def safe_filename(title, ext="txt"):
    stem = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()
    return f"{stem or 'untitled'}.{ext}"
