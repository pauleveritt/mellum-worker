"""Summarise a web server access log."""

import sys


def summarize(path, top=3):
    """Return {"status": {code: count}, "top_paths": [(path, count), ...]} for the log at `path`."""
    raise NotImplementedError


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    summary = summarize(argv[0], int(argv[1]) if len(argv) > 1 else 3)
    for code, count in sorted(summary["status"].items()):
        print(f"{code} {count}")
    for path, count in summary["top_paths"]:
        print(f"{count:>5} {path}")


if __name__ == "__main__":
    main()
