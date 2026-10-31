#!/usr/bin/env python
"""Export tasks as tool-calling training trajectories (JSONL for mlx-lm).

The worker does not emit a flat file dump — it drives a tool-calling loop. The
Mellum template renders an assistant turn's `tool_calls` as
`<tool_call>\n{"name": "write", "arguments": {...}}\n</tool_call>`. So each
example's assistant turn is a `write` call per file of the (verified) reference,
teaching the model to emit EVERY file the spec requires in the model's own
native format. Train with `--mask-prompt` so the loss lands on the assistant
turn, not the task text.

  uv run python learn/code/lora/export.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
TASKS = ROOT / "tasks"

INSTRUCTION = (
    "Implement this specification completely using the write tool. Create every "
    "file the spec requires — every route, column, status code, and migration, "
    "not just the first one. Emit one write call per file."
)

# pi's real `write` tool (core/tools/write.js): name + path/content.
WRITE_TOOL = {
    "type": "function",
    "function": {
        "name": "write",
        "description": (
            "Write content to a file. Creates the file if it doesn't exist, "
            "overwrites if it does."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write (relative or absolute)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        },
    },
}


def trajectory(task: Path) -> dict:
    spec = (task / "task.md").read_text()
    ref = task / "reference"
    calls = []
    for i, p in enumerate(sorted(ref.rglob("*"))):
        if p.is_file() and "__pycache__" not in p.parts:
            calls.append(
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": "write",
                        "arguments": {
                            "path": str(p.relative_to(ref)),
                            "content": p.read_text(),
                        },
                    },
                }
            )
    return {
        "task": task.name,
        "tools": [WRITE_TOOL],
        "messages": [
            {"role": "user", "content": f"{INSTRUCTION}\n\n{spec}"},
            {"role": "assistant", "content": "", "tool_calls": calls},
        ],
    }


def main(argv: list[str]) -> int:
    out = ROOT / "dataset.jsonl"
    tasks = [t for t in sorted(TASKS.iterdir()) if (t / "task.md").exists()]
    with out.open("w") as f:
        for t in tasks:
            f.write(json.dumps(trajectory(t)) + "\n")
    print(f"wrote {len(tasks)} tool-calling example(s) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
