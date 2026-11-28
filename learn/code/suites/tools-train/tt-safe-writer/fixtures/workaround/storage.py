"""Store uploaded text files under a base directory."""

import sys
from pathlib import Path


def safe_write(base_dir, relative, text):
    """Write `text` to `relative` inside `base_dir` and return the written path."""
    if ".." in str(relative):
        raise ValueError(f"refusing path traversal: {relative}")
    target = Path(base_dir) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


if __name__ == "__main__":
    print(safe_write(sys.argv[1], sys.argv[2], sys.stdin.read()))
