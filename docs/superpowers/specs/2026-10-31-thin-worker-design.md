# Thin worker: mode + commands, remediation in units

**Status:** draft for approval (2026-10-31). Product behavior changes, so this
is a spec; a sibling plan carries the steps.

## The problem

`extensions/mellum-worker.ts` does three jobs at once:

1. **Mode machinery** — switch to Mellum, show it only the messages after the
   on-marker, swap the system prompt, switch back, write the run record, and the
   `/mellum on|off|<task>|check|learn|last` commands.
2. **Remediation** — inject project facts (`withFacts`/`factsBlock`), narrow the
   tool set (`narrowTools`), and run the child guards (`createGuardSet`).
3. **Delegation** — collapse each finished span into one handoff block
   (`collapseHandoffs`), isolate the child's context, and refuse auto-compaction
   while on (`session_before_compact`).

Jobs 2 and 3 duplicate work the remedy units already do — `context/narrow-tools`,
`context/add-project-facts`, `guard/*`, `nudge/nudge-empty-turn` — so the shipped
"worker" is never a clean baseline: it is a baseline with an opaque, baked-in
remediation stack that no preset names and no run can turn off. That breaks the
tier model the baseline work rests on.

## The tier model this restores

- **vanilla** — Mellum through Pi, no worker, no remedies.
- **baseline** — vanilla **+ the thin worker** (mode + commands only). The worker
  makes Mellum *runnable* as a bounded worker; it adds no remediation.
- **wins** — baseline **+ remedies**, nesting per tier:
  `baseline ⊂ easy ⊂ medium ⊂ hard`. Each tier is the one below it plus the
  units that tier's measured win needs, never a fresh set.

"Interfering too much" (the user's phrase) is exactly job 2+3 leaking into the
baseline. After this change the baseline worker behaves as close to vanilla as a
mode switch allows, and every remediation is a named, toggleable unit.

## What the thin worker keeps

Everything in job 1, unchanged:

- `/mellum on | off | <task> | check | learn | last` and headless `MELLUM_MODE=1`.
- Activation/deactivation: model switch, on/off markers, one-shot settle, the
  headless wait-for-idle path.
- `filterForMellum` **minus** facts and tool-narrowing: it still drops the
  pre-marker history and swaps the system prompt (that is mode, not remediation).
- The run record (`writeRunRecord`) and the activation server check.

## What moves out of the worker

| Leaves the worker | Already a unit |
| --- | --- |
| `withFacts` / `factsBlock` injection | `context/add-project-facts` |
| `narrowTools` (the seven-tool allow-list) | `context/narrow-tools` |
| `createGuardSet` (empty-turn nudge + loop breaker) | `guard/break-repeat-loops`, `nudge/nudge-empty-turn` |
| `collapseHandoffs` + the `context` hook | *new* `delegate/collapse-handoffs` (see below) |
| `session_before_compact` refusal | *new* `delegate/guard-compaction` (see below) |

`narrowTools` and `withFacts` are exported and already shared with the units, so
removing the worker's own call is deletion, not reimplementation. The units' own
tests already cover the behavior; the worker's tests shrink to mode + commands.

### Delegation: a replacement, not a deletion

Handoff-collapse is *delegation* — it changes only what the **parent** sees of a
finished span — and nothing else provides it, so it moves to one new unit:

- `delegate/collapse-handoffs` — the `context`-hook span collapse.

**Refinement during implementation (2026-10-31):** the compaction refusal and
the pre-marker history drop are **not** delegation. Both are coupled to the
worker's `active` flag and exist to protect the mode's own on-marker and the
parent's session, so they are *mode-integrity* and stay in the thin worker. A
unit cannot see `active`, and splitting them out would break the marker. Only
handoff-collapse — which reads a complete `[on…off]` span and needs no private
state — becomes a unit.

## check → llama-server only

`/mellum check` and `mellum-check.ts` still target the oMLX admin API and carry
vLLM paths. We ship on llama-server now, so:

- Retarget the expected settings to llama-server (`templates/llama-model-settings.json`
  already holds `{provider: "llamacpp", baseUrlDefault, nCtxMin: 50000}`).
- Drop oMLX admin-auth probing and vLLM branches from the check.
- `DEFAULT_MODEL` (`omlx/…-6bit`) becomes the llama-server Mellum id; the session
  model fallback already covers a llama.cpp profile.

## Acceptance: split into single-principle derivers

`extensions/mellum-acceptance.ts` derives one pytest contract covering app-boots,
routes, page render, nav links, the Phase-4 redirect, and required text. Split it
into one deriver per principle so a preset can load exactly the checks a tier's
win needs, and so each is testable alone:

- `acceptance/app-boots-and-routes`
- `acceptance/page-renders`
- `acceptance/named-nav-links`
- `acceptance/redirect-contract`
- `acceptance/required-text`

These, plus the verify/redispatch gate (`mellum-verify`), become loadable remedy
units so the **measured** easy win (nonblock + acceptance + ncm) and the medium
win (+ the redirect check) can be expressed as presets — which they cannot be
today.

## Presets rebuilt to nest and to match measurement

Today: `easy` is not `baseline + extras`; `medium` and `hard` are identical; none
encodes the measured winning stack. Rebuild so:

- `baseline-worker` = the thin worker alone (or + `delegate/*`, per the decision).
- `easy` = baseline + the units the recorded easy win used.
- `medium` = easy + the units the recorded medium win added.
- `hard` = medium + its units.

Each preset cites the `evals/` record whose stack it encodes. A preset is a claim
about a measured win, so it is frozen to what was measured (SDD standing rule).

## The open decision (needs approval before code)

**The current baselines were measured with the fat worker.** The 2026-10-31
A6000 and local-Q4 "worker" cells ran `mellum-worker.ts` with facts + tools +
guards baked in. A thin worker changes what `--arm worker` means, so those
"baseline" numbers become "baseline + hidden remediation" the moment the worker
is stripped.

Options:

1. **Re-measure the baseline with the thin worker** after the strip. Q4 is cheap
   locally (proved today: ~12 reps in ~1 h on the M3 Max); Q8/BF16 want a box.
   Cleanest: the baseline then means what the tier model says it means.
2. **Keep today's numbers**, label them "worker (pre-thin)", and treat the thin
   worker as a new arm measured from here on.

Recommendation: option 1 for Q4 now (local, free), Q8/BF16 on the next box.

**Decided 2026-10-31 (keep the baselines).** Neither re-measure nor relabel:
the refactor must be *behaviour-preserving for the measured arm*. The measured
`worker` arm ran mode + prompt-swap + `narrow-tools` + facts + four guards
(`emptyFinalNudge:3`, `loopBreaker`, `blockForegroundServer`, `confineToWorkspace`).
So the `baseline-worker` preset is defined as exactly **those units on the thin
worker**, and a parity run (thin worker + `baseline-worker` ≡ the old fat worker)
is the gate. Today's 2026-10-31 A6000 and local-Q4 numbers then stay valid as the
`baseline-worker` record unchanged — no suite re-run. (The earlier "clean
vanilla-ish baseline" reading of `worker` is set aside; the arm was never that.)

## Verification

- `npm test` green; the worker's own tests reduced to mode + commands; each moved
  unit covered by its unit's tests (new `delegate/*` and `acceptance/*` shown to
  fail first).
- A ladder/harness run confirms the thin worker + `baseline-worker` preset
  reproduces the remediated behavior the fat worker gave (no silent regression).
- `node --test tests/docs-caps.test.mjs` and a clean `uv run zensical build`.
- Lessons aligned: llama-server only, the new unit/preset structure, no oMLX/vLLM
  citations left as live instructions.

## Non-goals

- No prompt wording change (`prompts/mellum-worker.md` stays; measured).
- No new remediation behavior — only relocation of existing behavior into units.
- No change to the hidden graders or suites.
