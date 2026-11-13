#!/usr/bin/env python3
"""Follow the newest ladder worker trace and print each turn live.

A ladder run writes its worker transcript to a fresh `trace.jsonl` per rung
(in a temp workspace). This tails the newest one and prints the worker's
thinking and tool calls as they happen, switching to the next rung's trace
automatically — so every rung is watchable in a terminal while the run goes.

Usage:  uv run python scripts/watch_ladder.py [extra_dir]   (Ctrl-C to stop)

`extra_dir` is an optional workspace/runs root to also watch for `trace.jsonl`,
for when a run writes traces outside the system temp dir.
"""
import glob
import json
import os
import sys
import tempfile
import time


def _globs() -> list[str]:
    # Derive from the ACTUAL temp dir so this works wherever tempfile puts ladder-*/ (not just
    # /tmp or /private/var/folders); keep the historical paths; add any dir given on the CLI.
    # A recursive glob over the whole temp dir is too slow to poll (macOS keeps
    # thousands of entries there), so temp roots match only ladder-*/ scratch dirs;
    # only a directory named on the CLI is searched recursively.
    roots = [tempfile.gettempdir(), "/tmp", "/private/var/folders/*/*/T"]
    pats: list[str] = []
    for r in roots:
        pats += [f"{r}/ladder-*/trace.jsonl", f"{r}/ladder-*/*/trace.jsonl"]
    for r in (a for a in sys.argv[1:] if not a.startswith("-")):
        pats.append(f"{r}/**/trace.jsonl")
    return pats


GLOBS = _globs()


def newest_trace():
    files = []
    for g in GLOBS:
        files += glob.glob(g, recursive=True)
    files = [f for f in files if os.path.exists(f)]
    return max(files, key=os.path.getmtime) if files else None


def find_assistant(obj):
    if isinstance(obj, dict):
        if obj.get("role") == "assistant" and "content" in obj:
            return obj
        for v in obj.values():
            r = find_assistant(v)
            if r:
                return r
    return None


def print_event(ev, turn):
    if not isinstance(ev, dict):
        return turn
    t = ev.get("type")
    if t == "tool_execution_start":
        print(f"     >> run {ev.get('name', '')}")
    elif t == "message_end":
        msg = find_assistant(ev) or {}
        content = msg.get("content", [])
        think, calls = [], []
        if isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if "toolCall" in b.get("type", ""):
                    args = json.dumps(b.get("arguments", {}))
                    calls.append(f"{b.get('name')}({args[:80]})")
                elif b.get("type") == "thinking":
                    think.append(str(b.get("thinking", "")).strip()[:120])
        turn += 1
        print(f"\n  ── turn {turn} [{msg.get('stopReason')}] ──")
        if think:
            print("     think:", " ".join(think)[:200])
        for c in calls:
            print("     CALL ", c)
    return turn


def main():
    cur = None
    fh = None
    turn = 0
    print("watching for ladder traces… (Ctrl-C to stop)")
    try:
        while True:
            nt = newest_trace()
            if nt and nt != cur:
                cur = nt
                if fh:
                    fh.close()
                fh = open(cur, "r")
                turn = 0
                print(f"\n========== {os.path.basename(os.path.dirname(cur))} :: {cur} ==========")
            if fh:
                where = fh.tell()
                line = fh.readline()
                if line:
                    line = line.strip()
                    if line:
                        try:
                            turn = print_event(json.loads(line), turn)
                        except json.JSONDecodeError:
                            fh.seek(where)  # partial line; retry next tick
                            time.sleep(0.2)
                    continue
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
