#!/usr/bin/env python3
"""Grounded docs lookup: a BM25 index over the installed venv packages.

The model fails exact-API contracts it cannot know — a library default (FastAPI's
`RedirectResponse` is 307, not the 303 a POST-redirect needs), a migration API, and
anything past its training cutoff (the ladder runs on Python 3.15). The truth is in the
venv that is actually running, so this indexes that venv's package source — every class
and function as a chunk carrying its signature (with default values) and docstring — and
answers a query with the top matches. Offline, dependency-free, reflects the exact
installed versions. It grounds on library docs a developer would have, never the task
solution or the hidden grader.

    python docs_lookup.py "RedirectResponse status code"      # auto-finds ./.venv
    python docs_lookup.py --site-packages <path> --k 5 "sqlite-utils migrate"
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SKIP_DIRS = {"__pycache__", "tests", "test", "testing", "_vendor", "site-packages"}
MAX_CHUNK = 1600
CACHE_NAME = "docs_bm25.json"

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, plus camelCase/snake_case sub-tokens so `RedirectResponse`
    matches `redirect` and `response` and `status_code` matches `status` and `code`."""
    out: list[str] = []
    for raw in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+", text):
        low = raw.lower()
        out.append(low)
        parts = [p for p in _CAMEL.sub(" ", raw).replace("_", " ").lower().split() if p]
        if len(parts) > 1:
            out.extend(parts)
    return out


def _chunk_text(node: ast.AST, source: str, qual: str) -> str:
    seg = ast.get_source_segment(source, node) or ""
    doc = ast.get_docstring(node) or "" if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) else ""
    head = seg[:MAX_CHUNK]
    return f"{qual}\n{head}\n{doc}"[:MAX_CHUNK]


def extract_chunks(py: Path, pkg_root: Path) -> list[dict]:
    """Each top-level + nested class/function in a module becomes one chunk."""
    try:
        source = py.read_text(errors="ignore")
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    module = str(py.relative_to(pkg_root).with_suffix("")).replace("/", ".")
    chunks: list[dict] = []

    def walk(node: ast.AST, prefix: str) -> None:
        for child in getattr(node, "body", []):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{module}:{prefix}{child.name}"
                chunks.append({"id": qual, "text": _chunk_text(child, source, qual)})
                if isinstance(child, ast.ClassDef):
                    walk(child, f"{prefix}{child.name}.")

    walk(tree, "")
    return chunks


def build_corpus(site_packages: Path) -> list[dict]:
    chunks: list[dict] = []
    for py in site_packages.rglob("*.py"):
        if any(part in SKIP_DIRS for part in py.relative_to(site_packages).parts[:-1]):
            continue
        if py.name.startswith("test_") or py.stat().st_size > 400_000:
            continue
        chunks.extend(extract_chunks(py, site_packages))
    return chunks


class BM25:
    """Minimal BM25 (Okapi), pure Python."""

    def __init__(self, docs_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = docs_tokens
        self.n = len(docs_tokens)
        self.lengths = [len(d) for d in docs_tokens]
        self.avgdl = (sum(self.lengths) / self.n) if self.n else 0.0
        self.tf: list[dict[str, int]] = []
        df: dict[str, int] = {}
        for d in docs_tokens:
            counts: dict[str, int] = {}
            for t in d:
                counts[t] = counts.get(t, 0) + 1
            self.tf.append(counts)
            for t in counts:
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query: list[str], i: int) -> float:
        counts, dl, s = self.tf[i], self.lengths[i], 0.0
        for t in query:
            f = counts.get(t, 0)
            if not f:
                continue
            denom = f + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / denom
        return s

    def top(self, query: list[str], k: int) -> list[tuple[int, float]]:
        scored = ((i, self.score(query, i)) for i in range(self.n))
        return sorted((x for x in scored if x[1] > 0), key=lambda x: x[1], reverse=True)[:k]


def signature(site_packages: Path) -> str:
    """A cheap fingerprint of the installed package set, so the index auto-rebuilds when the
    model installs (or removes) a package mid-run — the lookup must not go blind to new deps."""
    try:
        names = sorted(p.name for p in site_packages.iterdir())
    except OSError:
        names = []
    return hashlib.sha1("\n".join(names).encode()).hexdigest()


def load_index(site_packages: Path, rebuild: bool = False) -> list[dict]:
    cache = site_packages.parent / CACHE_NAME
    sig = signature(site_packages)
    if cache.exists() and not rebuild:
        try:
            data = json.loads(cache.read_text())
            if isinstance(data, dict) and data.get("sig") == sig:
                return data["chunks"]
            # stale: the installed packages changed since this cache was built — rebuild.
        except (ValueError, KeyError):
            pass
    chunks = build_corpus(site_packages)
    for c in chunks:
        c["tokens"] = tokenize(c["text"])
    try:
        cache.write_text(json.dumps({"sig": sig, "chunks": chunks}))
    except OSError:
        pass
    return chunks


def find_site_packages(start: Path) -> Path | None:
    for cand in sorted(start.glob(".venv/lib/python*/site-packages")):
        return cand
    return None


def lookup(query: str, site_packages: Path, k: int = 5, rebuild: bool = False) -> list[dict]:
    chunks = load_index(site_packages, rebuild=rebuild)
    bm = BM25([c.get("tokens") or tokenize(c["text"]) for c in chunks])
    hits = bm.top(tokenize(query), k)
    return [{"id": chunks[i]["id"], "score": round(s, 2), "text": chunks[i]["text"]} for i, s in hits]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("query", help="what to look up (library/API question)")
    p.add_argument("--site-packages", type=Path, default=None)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--rebuild", action="store_true")
    args = p.parse_args(argv)
    sp = args.site_packages or find_site_packages(Path.cwd())
    if not sp or not sp.is_dir():
        print("no venv site-packages found (pass --site-packages)", file=sys.stderr)
        return 2
    for hit in lookup(args.query, sp, k=args.k, rebuild=args.rebuild):
        print(f"\n### {hit['id']}  (score {hit['score']})")
        print(hit["text"].strip()[:700])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
