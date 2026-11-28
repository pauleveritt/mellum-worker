# 0009: Small-model pathologies are removed by Pi extensions first, training data second

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

A 1.5B model has less room for anything that gets in its way: long or unfamiliar contexts, long thinking, too
many tools, strict edit matching, escaping code inside JSON, vague error messages. Harness changes cost no GPU;
retraining costs hours. The audit of `r1d/data_sft_v1` found the data itself teaching a pathology: tool results
in the prompts were cut to 400 + 200 characters, so 31% of examples (987 of 3,173) show the model acting on a
result it saw only in part (median 1,280 characters hidden), while Mellum, whose action it copies, saw it whole.

## Decision

- **Train and serve the same shape.** Whatever the harness does to the context at inference, the training
  prompts do too (tool results cut exactly as `context/trim-tool-output` cuts them; the same tool set; the same
  system prompt). No cap in the data that the harness doesn't apply.
- **Harness first.** Each pathology the 1.5B shows is removed by a Pi extension (a remedy unit under
  `remedies/`, one small agnostic file) where one can do it; only what the harness can't fix goes into data.
- **Remedies already there to measure on the 1.5B:** `context/trim-tool-output`, `context/narrow-tools`,
  `context/use-short-prompt`, `context/repair-think-tags`, `prompt/think-briefly`, `guard/repeat-loops`,
  `guard/turn-cap`, `guard/whole-file-rewrite`; sampling at DeepSeek's recommended temperature 0.6, top-p 0.95.
- **New remedies to build when a screen shows the pathology** (each a lead until measured):
  - *show the file after a failed edit*: when `edit` finds no match, return the current text around the
    intended spot, so the model never repeats a blind edit (the re-read pathology, now fixed by data in Mellum);
  - *forgiving edit match*: accept an `oldText` that differs only in whitespace, and say so;
  - *tool-call rescue*: if a call arrives as unparsed marker text or with broken JSON escaping, recover it or
    answer with the one exact correction;
  - *small-model error messages*: tool errors rewritten to one short line naming the next action.
- **Carry to Mellum.** A remedy that helps the 1.5B is re-measured on Mellum (0008); it's never assumed to
  transfer, in either direction.
- The small-model preset (`remedies/presets/`) is the result of that measurement, added one unit at a time from
  the floor, as AGENTS.md requires.

## Consequences

`data_sft_v1` is superseded by a set built with inference-matched caps. Each new remedy needs a screen showing the
pathology before it is built, and a screen showing it fixed before it joins a preset.

## Evidence

The v1 audit numbers above (research note, 2026-11-28 log); the remedy units and their `meta` fields in
`remedies/`; `learn/pathologies.md`.
