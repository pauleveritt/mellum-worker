# One worker: Mellum Worker on Pi, no subagent, no OpenCode

Date: 2026-10-20. Decided with Paul: the Learning Center's vehicle is
`mellum-worker` and `/mellum`, and it is the delivery of the guardrails. The
pi-subagents Worker and the OpenCode port are removed, completely.

## What changes

- **Mellum Mode becomes Mellum Worker.** `extensions/mellum-mode.ts` is
  renamed, and the term changes in the templates, skill, docs and records'
  prose. The command stays `/mellum`; what Mellum receives — prompt, tools,
  guards, sampling — does not change.
- **The pi-subagents Worker is deleted**: `templates/pi/mellum-worker.agent.md`,
  the skill's `05-worker-pi.md` phase, the intercom option, the child-only
  guard loading, and the Worker run-record writer.
- **Worker records are deleted**: the writer, the readers in `learn` and
  `last`, their fixtures and tests. Old files on disk are not touched; the
  code stops reading or writing `kind: "worker"` records.
- **The OpenCode port is deleted**: `opencode/plugin.js`,
  `templates/opencode/`, the skill's `04-provider-opencode.md` and
  `05-worker-opencode.md`, the `opencode-plugin` package fields, and its
  tests and docs.
- **The ladder's `delegated` mode is deleted**, with its mirror-profile code
  and its summarize columns. Measured records in `evals/` stay as
  evidence; no record is rewritten or removed.

## What stays

- `/mellum`, the extension's guards, the prompt and the seven tools.
- The measured records, the ladder's other modes, and the Learning Center.
- The setup skill, reduced to Pi: preflight, weights, server, provider,
  rules, smoke, project facts.

## Non-goals

- Any change to what Mellum receives, or to the ladder's scoring.
- Rewriting or deleting measured evidence.
- A new OpenCode story, or a new subagent.

## Consequences

- A breaking release: the package is Pi-only and the term is new. The tag
  and README install lines move together when this ships.
- A reader of an old Worker run record is no longer served by `learn` or
  `last`; this is deliberate, and the changelog says so.

## Tests

The rename keeps the extension's tests, updated. The removals delete their
tests with their code and add one test that the removed surfaces are gone:
no subagent template, no OpenCode file, no `delegated` mode choice, and no
`kind: "worker"` branch in `learn`.
