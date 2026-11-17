#!/usr/bin/env python
"""Verify a task: independence guard, then every requirement passes.

A task enters the dataset only when this exits 0 — the guard finds no
hard-suite literal, and the reference satisfies every requirement (no ghosts).

Run with the stack deps available, e.g.:
  uv run --with 'fastapi[standard]' --with sqlite-utils --with jinja2 \
          --with httpx --with pytest python learn/code/lora/verify.py <task-dir>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: verify.py <task-dir>", file=sys.stderr)
        return 2
    task = Path(argv[1])
    guard = subprocess.run([sys.executable, str(HERE / "guard.py"), str(task)])
    if guard.returncode != 0:
        return guard.returncode
    checks = task / "checks.py"
    if not checks.exists():
        print(f"no checks.py in {task}", file=sys.stderr)
        return 2
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rA", str(checks)]
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
