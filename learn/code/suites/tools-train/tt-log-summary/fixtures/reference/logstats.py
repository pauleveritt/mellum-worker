"""Summarise a web server access log."""

import re
import sys
from collections import Counter

LINE = re.compile(r'"\S+ (?P<path>\S+) [^"]*" (?P<status>\d{3}) ')


def summarize(path, top=3):
    """Return {"status": {code: count}, "top_paths": [(path, count), ...]} for the log at `path`."""
    status = Counter()
    paths = Counter()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = LINE.search(line)
            if not match:
                continue
            status[int(match["status"])] += 1
            paths[match["path"].split("?", 1)[0]] += 1
    ranked = sorted(paths.items(), key=lambda item: (-item[1], item[0]))
    return {"status": dict(status), "top_paths": ranked[:top]}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    summary = summarize(argv[0], int(argv[1]) if len(argv) > 1 else 3)
    for code, count in sorted(summary["status"].items()):
        print(f"{code} {count}")
    for path, count in summary["top_paths"]:
        print(f"{count:>5} {path}")


if __name__ == "__main__":
    main()
