# 0014: Run records carry the prompt, the tools and the weights the model was actually served

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

A run record named the remedy units and the hash of each extension file, which rebuilds the system prompt and
tool schemas only with this repository at that commit. Pi assembles both at run time; the exact payload sat in
`trace.jsonl`, which is never committed. A reviewer asked for the prompt and tools in the manifest, so another
harness (OpenCode, or a plain test) can use the same ones. Checking the scoreboard showed a second gap: every
llama.cpp run reports the same served name, `llamacpp/Mellum2.1-12B-A2.5B-Thinking`, whether it served base
Mellum, mix120, the tools tune, Tsunami or round 2, so recorded runs would blend different tunes into one row.

## Decision

- `ladder/ladder/surface.py` reads the first request of a trace: `system_prompt`, `tools`, their sha256s, the
  `chat_template_kwargs` sent (the thinking switch) and whether later requests changed any of it. The ladder's
  per-rung `run.json`, the learn harness's `run.json` and the eval `manifest.json` (`surfaces`, deduplicated with
  the runs that used each) all carry it.
- The harness asks the server what it is serving (`/v1/models`, and llama.cpp's `/props` for the weights file,
  context size and template hash) and records it as `served` in `run.json`.
- Scoreboard entries gain `thinking`, `tool_errors`, `weights` and `surface`; the board groups by served name
  plus weights plus thinking mode. Each distinct prompt and tool set is stored once in
  `evals/scoreboard/surfaces/`, with the run's own workspace path as `{workspace}`.
- `learn/code/surface_probe.py` sends any manifest's prompt and tools to any model and names each faulty call.

## Consequences

Older runs are filled from their traces where the trace still exists. Their weights are known only from the
batch folder, so only batches whose model is certain were recorded (base, mix120, tools, Tsunami per ADR 0003,
round 2, the 1.5B, the teacher); the others wait for a confirmed label. All 307 recorded runs used one tool set
and one prompt apart from the workspace path.

## Evidence

Tests shown red first: `ladder/tests/test_surface.py`, `ladder/tests/test_runner.py`,
`learn/code/tests/test_harness.py`, `learn/code/tests/test_scoreboard.py`, `learn/code/tests/test_surface_probe.py`,
`scripts/baseline/tests/test_baseline.py`. Live check: the lab Mellum on Pi's recorded prompt and tools gave 10/10
well-formed calls through `surface_probe.py`.
