"""Render a list of dicts as a Markdown table."""

import json
import sys


def render(rows, align=None):
    """Return the Markdown table for `rows` (a list of dicts) as a string ending in a newline."""
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in rows:
        lines.append("| " + " | ".join(str(row[c]) for c in columns) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        print(render(json.load(handle)), end="")
