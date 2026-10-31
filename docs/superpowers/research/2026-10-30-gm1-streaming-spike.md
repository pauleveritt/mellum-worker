# GM.1 streaming spike: a code panel that streams the worker's edits

**2026-10-30.** Guided mode's first phase
([spec](../specs/2026-10-30-guided-mode-design.md)) carried one real risk: can a
Pi TUI panel show the worker's edits as they land, or does it fight the agent
loop? This note records the spike that settled it.

## What is measured / what is conjecture

**Measured (this spike, n = 1, Pi 1.4.0, local 6-bit Mellum on llama.cpp):**

- A `ctx.ui.setWidget(key, string[])` panel renders a numbered code view above
  the editor and **coexists with the chat** — it does not take keyboard focus
  the way `ctx.ui.custom` does, so the worker runs while the panel is up.
- A `pi.on("tool_call", …)` handler fires on the worker's `edit`/`write` call;
  re-reading the file and calling `setWidget` again **repaints the panel to the
  new contents**. Seen live: the worker changed `return a - b` to `return a + b`
  and the panel went from "watching" to "updated" with the new line, the chat
  still running beside it.
- The extension loads clean on Pi 1.4.0 (installed to a scratch prefix; the
  shipped pin stays 1.3.0 until GM.2).

**Conjecture / not yet measured:**

- Token-by-token streaming *within* a single edit. The spike repaints on the
  *completed* edit — the spec's named fallback — which reads cleanly; mid-edit
  streaming is untried and may not be worth it.
- Several edits in one turn, or a `write` of a new file, beyond the one-edit case.

## The spike

A throwaway `pi -e` extension (not shipped; removed after it validated the
approach — in git history):
`/gmspike <file>` opens the panel, and the `tool_call` handler repaints it when
the worker edits that file. Driven against a scratch `add.py` with the real
local Mellum: "edit add.py so add returns a + b". The worker ran `ls`, read the
file, made the one-line `edit`, and the panel repainted.

## Decision

Guided mode's code panel is a `setWidget` string-array panel, repainted from the
file on each completed `edit`/`write` tool call — not a focused `custom`
overlay. The file on disk is the source of truth, so a worker edit and a hand
edit show up the same way. GM.2 (move the course pin to Pi 1.4) and GM.3 (S0
interactive) build on this.

## What would falsify this / risks

- A panel that flickers or lags under many edits per turn would push us back to
  a custom component with its own buffer. Not seen at n = 1.
- `setWidget` placement and height on a small terminal are untested; a long file
  may need truncation or scrolling.
- The spike repaints 150 ms after `tool_call`; a slow disk or a large file could
  show a stale frame. Repainting on a post-edit event instead would remove the
  guess.
