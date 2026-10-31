# Small-model tool-calling: the format floor vs the capability floor

Date: 2026-10-26. Status: measured findings while standing up new local models
(Qwen3-Coder, a 1.5B distill) against the flow harness via oMLX. Companion to
the `content-tool-call-assist` extension and
[2026-10-19-small-model-tool-presentation.md](2026-10-19-small-model-tool-presentation.md).

## What is measured

Driving each model through oMLX (`:8001/v1`, OpenAI-completions) with a `write`
tool defined:

- **DeepSeek-R1-Distill-Qwen-1.5B-4bit emits tool INTENT as text, never a
  structured call.** Given a tool, it returns `tool_calls: None` and writes the
  call in content — first as prose (`get_weather(Paris)`), and when pushed for a
  fenced JSON block, as `{"tool":"write","args":["a.py","hi"]}` with a POSITIONAL
  LIST for args. Taught the exact Hermes format, it put the JSON in a markdown
  explanation instead of calling. Native context 131072; decode ~220 tok/s.
- **The `content-tool-call-assist` shim closes the FORMAT gap.** It promotes a
  text call into a real one, and (fixed this session) maps a positional list onto
  the tool's declared parameter order and converts Hermes/Qwen XML to the same
  named-args JSON object. A list it cannot map, or a bare scalar, is now rejected
  so the loop re-prompts instead of sending the server an invalid call (the old
  code let an array through — `typeof [] === "object"` — and the server 422'd
  "arguments must be a JSON object, got list", crashing the run). Pure parser
  split into `parse.ts` with a unit-test suite.
- **The 1.5B is still below the CAPABILITY floor.** With the shim working, it
  tool-calls but emits INCOMPLETE calls — `write` with a `path` and no `content`
  — repeats that on every retry, and leaks DeepSeek tool-channel tokens. It
  thrashes on even a trivial one-file write; no file is produced.
- **Qwen3-Coder-30B-A3B-Instruct-4bit tool-calls NATIVELY and correctly.**
  `tool_calls` returns a complete `write(path, content)` with properly escaped
  content, `finish_reason=tool_calls`, no shim needed — it drives the harness
  exactly like Mellum. Footprint 16.2 GB weights (unified memory), KV ~6 MB per
  64 tokens, decode ~80–85 tok/s (same ballpark as Mellum despite 30B, because
  4-bit MoE with ~3B active). The 6-bit (~24.8 GB) is also downloaded.

## What is conjecture

- There are TWO floors for tool-driven agent work, and they are different. The
  **format floor** — emitting a structured, parseable call — the shim lowers to
  "the model writes the call somewhere in its text." The **capability floor** —
  forming a COMPLETE, correct call (all required args) and sustaining a multi-
  step loop — the shim does nothing for; a 1.5B reasoning distill sits below it.
- An instruct/coding model clears both floors even when small-ish and heavily
  quantised (Qwen3-Coder 30B-A3B-4bit, ~3B active), where a same-era 1.5B
  reasoning distill clears neither. Tool-use training and task type look to
  matter more than raw parameter count for this harness.

## What would falsify this / Risks

- A different small model that is instruct-tuned for tools (not an R1-style
  reasoning distill) might clear the capability floor at ~1.5–3B — untested here;
  the 2B distill and gemma-4-e2b in cache are the next probes.
- The shim's `ASSIST_FORCE_TOOLS` retry path might coax complete args out of the
  1.5B if the nudge carried the full argument SCHEMA (names + required), not just
  tool names — not yet tried; could lower the capability floor a little.
- Qwen3-Coder's hidden-grade RESULTS on the hard suite are not in yet (a run is
  in flight); "tool-calls natively" is a capability finding, not a pass-rate.
  The Qwen-vs-Mellum (and 4-bit vs 6-bit) comparison is the measurement to come,
  under the free/forced and memory preregistrations already recorded.
