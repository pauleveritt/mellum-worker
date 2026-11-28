#!/usr/bin/env python
"""Agnostic smoke check for a built project: it parses, it imports, its templates parse.

No routes, no values, no suite knowledge — just "does the code the worker wrote actually load".
The plan loop has no per-step gate, so a build that does not parse (a Jinja `{{ extends }}` where a
`{% extends %}` was meant) or does not import (`from fastapi import HTMLResponse` — wrong module)
ships as a silent zero. This pass catches those two structural classes cheaply. It does NOT check
behaviour — wrong text, wrong status — that is the hidden grader's job.

Three stages, each failing fast on the first offending file:
  1. parse   — ast.parse every .py.
  2. import  — exec every top-level .py module (so an import error or a bad top-level call shows).
  3. render  — jinja2-parse every template.

Prints `SMOKE_OK` and exits 0 when all pass; prints `SMOKE_FAIL: <file>: <error>` and exits 1 on
the first failure. Run from the project root (or pass it as argv[1]).
"""
import ast
import importlib.util
import os
import sys

SKIP_DIRS = {
    ".venv", "venv", "env", ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "node_modules", "dist", "build", ".tox", "grader_tests",
}
SKIP_IMPORT_STEMS = {"conftest", "setup", "__init__"}
TEMPLATE_EXT = (".html", ".htm", ".j2", ".jinja", ".jinja2")


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            yield os.path.join(dirpath, name)


def fail(path, e):
    print(f"SMOKE_FAIL: {path}: {type(e).__name__}: {e}")
    return 1


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."

    # 1. parse every .py
    for path in walk(root):
        if path.endswith(".py"):
            try:
                with open(path, encoding="utf-8") as fh:
                    ast.parse(fh.read(), filename=path)
            except (SyntaxError, ValueError, UnicodeDecodeError) as e:
                return fail(path, e)

    # 2. import every TOP-LEVEL .py module, so an import error or a broken top-level call surfaces.
    # Only root-level modules (not package internals), with __name__ != "__main__", so a guarded
    # `uvicorn.run(...)` under `if __name__ == "__main__"` does not fire. Best effort and agnostic:
    # a src-layout app with no root modules is simply not import-checked here.
    sys.path.insert(0, os.path.abspath(root))
    for name in sorted(os.listdir(root) if os.path.isdir(root) else []):
        if not name.endswith(".py"):
            continue
        stem = name[:-3]
        if stem in SKIP_IMPORT_STEMS or stem.startswith("test_") or stem.endswith("_test"):
            continue
        path = os.path.join(root, name)
        try:
            spec = importlib.util.spec_from_file_location(stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            return fail(path, e)

    # 3. parse every template (syntax only — no render, no context needed)
    try:
        from jinja2 import Environment
    except Exception:
        print("SMOKE_OK (python only; jinja2 unavailable)")
        return 0
    env = Environment()
    for path in walk(root):
        if path.lower().endswith(TEMPLATE_EXT):
            try:
                with open(path, encoding="utf-8") as fh:
                    env.parse(fh.read())
            except Exception as e:
                return fail(path, e)

    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
