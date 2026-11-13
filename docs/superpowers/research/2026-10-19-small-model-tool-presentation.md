# Learning: presenting tools to a small model — stripping the native tool field regresses tool calling

Date: 2026-10-19
Status: settled (negative result). The change was reverted.

## Hypothesis

The model template renders the host's tool declarations as a single run-on line
with every separator trimmed (no line feeds between declarations). The guess was
that this wall of schema hurts a small model, and that **taking over tool
presentation in the assist plugin** — stripping the request's native tool field
so the template emits no tool block, and instead listing each tool on its own
legible line in the system nudge — would lift pass rates.

## Setup

- Model: Gemma E2B (4-bit MLX) served over an OpenAI-compatible endpoint, driven
  through the content-tool-call-assist plugin (force mode).
- Ladder: `--mode direct --profile tuned --rung 1..5 --repeat 3 --deadline 150
  --thinking off`. Scored by the frozen per-rung checks.
- Arms:
  - **Baseline** — native tool field kept in the transcript; the nudge adds only
    the output-shape contract and the tool names.
  - **Strip** — native tool field removed from the transcript; the nudge carries
    a compact, line-fed tool spec (one `name(params) — desc` line per tool).

## Result

| arm | rungs 1–5 × n=3 | notes |
|-----|-----------------|-------|
| baseline | **5/15** (r1 3/3, r3 2/3) | the working config |
| strip | **0/15** (every rung 0/3) | total collapse |

The strip arm produced a smaller, cleaner prompt (≈13,900 → 6,903 chars on the
first turn, one legible line per tool) — and it was strictly worse.

## Why it collapsed

Stripping the tool field is **not separable from execution and history
rendering** in this host. The same transcript tools drive how a tool-*result*
turn is rendered. With the declarations removed, the first one or two calls still
work, but as soon as a tool result enters the history the template renders a
tool-response block referencing tools it no longer knows about; the prompt is
malformed and the model answers with an empty turn, and the loop dies.

Trace, rung 1 (strip arm):

```
assistant[toolUse] call ls    → EXECUTE ls   → result: .git/ calculator.js …
assistant[toolUse] call read  → EXECUTE read → result: export function totalCents…
assistant[toolUse] (empty)    ← dies: no call, no text, right after the result
```

Baseline and strip differed by exactly this one change, so the collapse is
attributable to it.

## Decision

- **Reject and revert the strip.** Keep the host's native tool field in the
  transcript; it is load-bearing for both execution and tool-result rendering.
- The missing line feeds in the template's tool block are a real cosmetic defect
  but **not** the cause of the failures — the native format, ugly as it is, is
  what the model was trained against and what the host needs.
- The assist plugin's nudge stays minimal: the output-shape contract plus the
  tool names. It does not re-present the schema.

## Leads this surfaced (not changed here)

- Two tools in the set (`find`, `grep`) shell out to binaries that are
  unavailable offline, so they can never succeed and can lure a first call into
  a dead end. Candidate for a separate, measured trim.
- The rung-2 failures are a different, prompt-addressable cause: the worker
  deletes or rewrites an existing test instead of adding alongside it, which the
  check rejects (`tests_unchanged: false`). Tracked as its own change.
