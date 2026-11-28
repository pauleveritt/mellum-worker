"""Very small search helpers."""
from textkit.normalize import normalize_text


def matches(query, document):
    return normalize_text(query) in normalize_text(document)


def search(query, documents):
    return [doc for doc in documents if matches(query, doc)]
