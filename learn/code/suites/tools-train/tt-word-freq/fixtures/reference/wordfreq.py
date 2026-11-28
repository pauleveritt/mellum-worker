"""Count word frequencies in a text file."""

import re
import sys
from collections import Counter

WORD = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")


def count_words(text):
    """Return [(word, count), ...], most frequent first."""
    words = WORD.findall(text.lower())
    return sorted(Counter(words).items(), key=lambda item: (-item[1], item[0]))


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
