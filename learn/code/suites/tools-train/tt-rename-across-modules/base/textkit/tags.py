"""Tag handling."""
from textkit import normalize


def unique_tags(tags):
    seen = []
    for tag in tags:
        tag = normalize.clean(tag)
        if tag and tag not in seen:
            seen.append(tag)
    return seen
