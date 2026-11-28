"""Summarise a web server access log."""

import sys
from collections import Counter


def summarize(path, top=3):
    """Return {"status": {code: count}, "top_paths": [(path, count), ...]} for the log at `path`."""
    status = Counter()
    paths = Counter()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 9:
                continue
            status[int(parts[8])] += 1
            paths[parts[6]] += 1
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
