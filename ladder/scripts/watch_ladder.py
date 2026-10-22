#!/usr/bin/env python3
"""Follow the newest ladder worker trace and print each turn live.

A ladder run writes its worker transcript to a fresh `trace.jsonl` per rung
(in a temp workspace). This tails the newest one and prints the worker's
thinking and tool calls as they happen, switching to the next rung's trace
automatically — so every rung is watchable in a terminal while the run goes.

Usage:  python scripts/watch_ladder.py        (Ctrl-C to stop)
"""
import glob
import json
import os
import sys
import time

GLOBS = [
    "/private/var/folders/*/*/T/ladder-*/trace.jsonl",
    "/private/var/folders/*/*/T/ladder-*/*/trace.jsonl",
    "/tmp/ladder-*/trace.jsonl",
    "/tmp/ladder-*/*/trace.jsonl",
]


def newest_trace():
    files = []
    for g in GLOBS:
        files += glob.glob(g)
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
