"""Tag handling."""
from textkit import normalize


def unique_tags(tags):
    seen = []
    for tag in tags:
        tag = normalize.normalize_text(tag)
        if tag and tag not in seen:
            seen.append(tag)
    return seen
