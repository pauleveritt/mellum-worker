"""Very small search helpers."""
from textkit.normalize import clean


def matches(query, document):
    return clean(query) in clean(document)


def search(query, documents):
    return [doc for doc in documents if matches(query, doc)]
