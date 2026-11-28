"""Count word frequencies in a text file."""

import sys
from collections import Counter


def count_words(text):
    """Return [(word, count), ...], most frequent first."""
    return Counter(text.split()).most_common()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0]
    top = int(argv[1]) if len(argv) > 1 else 10
    with open(path, encoding="utf-8") as handle:
        counts = count_words(handle.read())
    for word, count in counts[:top]:
        print(f"{word} {count}")


if __name__ == "__main__":
    main()
