# New features, and how each is proven

Everything built this round, and the evidence that it works. The rule in this
repo is the same for every feature: **prove it with a real oracle, never by
self-report.** A pure function is proven by a unit test that fails first; an
extension by unit tests plus a dispatch test; a document/vision extractor by
running it against a real file; the dashboard by driving the real UI and real
endpoints; a ladder rung by a reference solution passing the hidden oracle; a
prompt change by measuring the ladder with and without it.

Full suite: **379 node tests pass**, **218 ladder tests pass**.

## Ladder rungs 10–12 (new gates)

- **What.** Rung 10 Archive & Audit (a destructive-archive decoy off the
  write-list), rung 11 reporting over a pre-filled database (an archived-but-open
  trap row), rung 12 summing two columns of a file far larger than the context
  window (must be streamed).
- **How proven.** (1) *Winnable and real* — a reference solution passes the
  hidden cumulative oracle (`_hidden_p1..pN`) plus the frozen acceptance test:
  "15 passed" for each. (2) *Wired* — the ladder's own pytest suite (218) covers
  registration and fixtures. (3) *A worker clears them* — the 6-bit passed all
  three 3/3 mediated, recorded with raw stripped in
  `evals/2026-10-21-rungs-10-12-6bit/`.
- **Status.** Shipped.

## Extensions (opt-in Pi extensions, loaded with `--pi-extension`)

Each is self-contained (Node + Pi hooks, no framework coupling); the pure core
is unit-tested, and the ones that touch the outside world are also run for real.

- **mellum-context** — SQLite FTS5 context intelligence (chunking, BM25 with a
  recency boost, chronological ordering, a `context_search` tool).
  *Proven:* `tests/mellum-context.test.mjs` — **12 passing** (chunking, rank
  monotonicity, temporal ordering, FTS5 search, re-index replaces).
- **mellum-rethink** — skeptical push-back: parses human claims, checks them
  against ground truth, pushes back on contradictions.
  *Proven:* `tests/mellum-rethink.test.mjs` — **10 passing** (claim parsing,
  contradiction detection, "cannot verify ≠ accuse", push-back message).
- **mellum-files** — PDF / Word / Excel extraction via a pure-Node zip reader and
  `node:zlib`.
  *Proven:* `tests/mellum-files.test.mjs` — **10 passing** (central-directory zip
  walk, docx/xlsx/pdf text, FlateDecode) **plus a live smoke** against real
  deflated `.docx`/`.xlsx` built with Python `zipfile`.
- **mellum-vision** — local vision model (default `Qwen3.8-2B-Distill`) for
  images and screenshots; auto-downloads via its repo id.
  *Proven:* `tests/mellum-vision.test.mjs` — **5 passing** (argv, output parsing
  on a real mlx_vlm sample) **plus end-to-end**: the model ran locally and
  correctly described the dashboard screenshot.
- **mellum-override** — edit the worker's system prompt live from a file the
  dashboard writes.
  *Proven:* `tests/mellum-override.test.mjs` — **6 passing** (parse, replace,
  append, insert-when-absent) **plus live**: typed in the dashboard, saved,
  persisted, and the nudge was seen in the worker's actual trace (16 occurrences).

## The UX surface (slash commands and model tools)

- **What.** `/index`, `/context`, `/read-file`, `/see`, `/replay`, plus the
  `context_search`, `read_document`, `describe_image` tools, and the control
  hooks.
- **How proven.** `tests/mellum-ux-commands.test.mjs` — **7 passing**: a fake Pi
  harness captures each extension's registered commands/tools/hooks and
  dispatches them against temp files (no real home dir, no model load) — e.g.
  `/index` then `/context` finds the passage, `describe_image` rejects a
  non-image without running the VLM, `/replay` warns on an empty feed.

## The dashboard (`dashboard/`, dependency-free stdlib server + tina4js page)

- **What.** Live rung grid, click-a-rung drill-down (past runs + summaries), an
  intelligence centre (told-vs-truth from `mellum-rethink`), a live system-prompt
  editor, Play/Pause wired to `mellum-control`, and one "Start full ladder run"
  button.
- **How proven.** The oracle is the real UI against the real endpoints, verified
  in the browser: `/rung` drill-down opened on rung 5 and showed its three past
  runs; `/override` round-tripped (typed → saved → re-read); `/control` toggled
  play↔pause; the full-ladder button launched a real sweep; and the grid filled
  live from `run.json` as the worker ran. Endpoint round-trips confirmed with
  `curl`.
- **Status.** Shipped; wired to a live run via `mellum-feed`/`mellum-control`/
  `mellum-override` so the controls drive a real worker, not just a viewer.

## Worker prompt v8 — the run-all-tests nudge

- **What.** The "how to check" step now tells the worker to run the **whole**
  named test file and pass **every** test in it, never a single `::test_function`
  — fixing the self-narrowing habit that failed rungs 4/5.
- **How proven.** (1) *Diagnosed from the trace* — the worker ran the file, then
  narrowed pytest to one test and self-certified on that subset. (2) *Fix proven
  before shipping* — the same nudge (via `mellum-override`) flipped rungs 4 and 5
  from 0/1 to PASS un-mediated (rung 4: full three-file fix, 53 s; rung 5: decoy
  untouched, 90 s), no frozen test, no redispatch. (3) *Baked in and
  regression-checked* — committed as v8, templates rebuilt (drift test green),
  and re-measured across the full ladder to confirm it lifts 4/5 without
  regressing other rungs.
- **Status.** Shipped; the full-ladder regression sweep is the standing check
  that it helps without harm.

## The honest line

A feature is "proven" here only to the degree its oracle is real. Unit tests
prove the pure logic; a live run proves the integration; the ladder proves a
prompt or worker change against a frozen, external, unweakenable test — never
against the worker's own "I'm done." That is the same discipline the whole
project rests on, applied to its own features.
