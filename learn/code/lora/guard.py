#!/usr/bin/env python
"""Independence guard for the LoRA completeness-probe dataset.

Rejects any task file carrying a hard-suite DOMAIN literal. The shared stack
(FastAPI, Jinja2, SQLite, TestClient, sqlite-utils) is allowed on purpose —
only the AgentClinic complaints domain must not leak into a training task.

Usage: python guard.py <task-dir>   (exit 0 clean, 1 on a hit)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Multi-char paths / names / phrases: plain case-insensitive substring.
BANNED_PHRASES = [
    "agentclinic",
    "come in. sit down",
    "/complaints",
    "/report",
    "/stats",
    "/visits",
    "/archive",
    "/resolve",
    "/reopen",
    "idx_tickets_status_archived",
    "add_tickets_note",
    "add_tickets_status_archived_index",
    "backfill_resolved_at",
    "create_open_tickets_view",
    "open_tickets",
    "all_time_total_cents",
    "archived_total_cents",
    "open_total_cents",
    "min_minutes",
    "_sqlite_migrations",
    "resolved_at",
    "archived_at",
    "agent_name",
]

# Short identifier tokens: word-boundary match, so "notes" does NOT trip "note".
BANNED_TOKENS = [
    "agentclinic",
    "complaint",
    "complaints",
    "tickets",
    "ticket",
    "archived",
    "archive",
    "resolve",
    "resolved",
    "reopen",
    "audit",
    "seq",
    "cents",
    "visits",
    "note",  # the hard suite's `note` column; \bnote\b won't match "notes"
]

# Files worth scanning (skip binaries, caches).
SCAN_SUFFIXES = {".py", ".md", ".html", ".json", ".txt", ".toml", ".sql"}


def scan_text(text: str) -> list[str]:
    low = text.lower()
    hits = []
    for p in BANNED_PHRASES:
        if p in low:
            hits.append(p)
    for t in BANNED_TOKENS:
        if re.search(rf"\b{re.escape(t)}\b", low):
            hits.append(t)
    return hits


def check_task(task_dir: Path) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in sorted(task_dir.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if "__pycache__" in path.parts:
            continue
        hits = scan_text(path.read_text(encoding="utf-8", errors="ignore"))
        if hits:
            findings[str(path.relative_to(task_dir))] = sorted(set(hits))
    return findings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: guard.py <task-dir>", file=sys.stderr)
        return 2
    task_dir = Path(argv[1])
    if not task_dir.is_dir():
        print(f"not a directory: {task_dir}", file=sys.stderr)
        return 2
    findings = check_task(task_dir)
    if findings:
        print(f"LEAK: {task_dir} carries hard-suite literals:")
        for f, hits in findings.items():
            print(f"  {f}: {', '.join(hits)}")
        return 1
    print(f"clean: {task_dir} shares no hard-suite domain literals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
