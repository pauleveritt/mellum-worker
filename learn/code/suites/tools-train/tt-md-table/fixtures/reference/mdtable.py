"""Render a list of dicts as a Markdown table."""

import json
import sys


def _numeric(values):
    present = [v for v in values if v is not None]
    return bool(present) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in present)


def _cell(value):
    return "" if value is None else str(value).replace("|", "\\|")


def _rule(width, side):
    if side == "right":
        return "-" * (width - 1) + ":"
    if side == "center":
        return ":" + "-" * (width - 2) + ":"
    return ":" + "-" * (width - 1)


def _pad(text, width, side):
    if side == "right":
        return text.rjust(width)
    if side == "center":
        return text.center(width)
    return text.ljust(width)


def render(rows, align=None):
    """Return the Markdown table for `rows` (a list of dicts) as a string ending in a newline."""
    align = align or {}
    columns = list(dict.fromkeys(key for row in rows for key in row))
    sides = {c: align.get(c) or ("right" if _numeric([r.get(c) for r in rows]) else "left") for c in columns}
    cells = [[_cell(r.get(c)) for c in columns] for r in rows]
    widths = [max([3, len(c)] + [len(line[i]) for line in cells]) for i, c in enumerate(columns)]

    def line(values):
        return "| " + " | ".join(_pad(v, w, sides[c]) for v, w, c in zip(values, widths, columns)) + " |"

    out = [line(columns), "| " + " | ".join(_rule(w, sides[c]) for w, c in zip(widths, columns)) + " |"]
    out += [line(values) for values in cells]
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        print(render(json.load(handle)), end="")
