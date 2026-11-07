# Pi's extension surface against our units: persuasion or enforcement?

## For Andre

- **What this is:** a code reading of Pi 1.4.0's extension hooks next to the 21 remedy units on
  `integration`, sorting each unit as persuasion (text only), enforcement (a hook that blocks,
  rewrites or guarantees) or mixed (a guaranteed trigger whose fix is text). Nothing was run.
- **The count:** 5 persuasion, 10 enforcement, 5 mixed, 1 affordance.
- **The top five guarantees to build** (ranked, all unmeasured, each would be its own R cycle):
  compile/import checks; fix the settle layer; a mediated test for Easy; an idle-bounded `bash`;
  `PATH` fixed once with `spawnHook`.
- **Correction (2026-11-07):** a first draft on the old branch said thinking is off in the rig.
  It is **on** in the harness: F.1's payloads carry `chat_template_kwargs.enable_thinking: true`
  ([record](../../../evals/2026-11-07-f1-payload/table.md)). Only `scripts/screen.sh` passes
  `--thinking off`.

**What is measured.** Nothing run for this note. Pi at tag `v1.4.0` (paths under
`packages/coding-agent/src/core/`, or `packages/agent/src/` when they start `agent/`), read
2026-11-07 on the old branch; line numbers were not re-read. This repo's side was re-checked on
`integration` (`736684c`). The thinking correction comes from F.1's recorded payloads.

**What is conjecture.** Every ranking, mechanism and cost. Pathology counts cite notes that
live only on the unmerged `lc40-thin-worker` branch (n = 6–12, one host); they are leads.

## Ladder run

None. This note decides nothing; each guarantee below gets its own preregistered R cycle (rung,
arms, n, rule) before it ships.

## Persuasion → enforcement

| Class | Units on `integration` | Hook |
| --- | --- | --- |
| persuasion (5) | `prompt/name-the-layout`, `verify-the-spec`, `python-developer`, `concept-sketch`; `context/use-short-prompt` | `before_provider_request` adds or swaps text |
| enforcement (10) | `guard/exists`, `foreground-server`, `outside-workspace`, `repeat-loops`, `whole-file-rewrite` | `tool_call` block (the block is guaranteed; what to do next is prose) |
| | `tool/background-long-commands` | `tool_call` rewrites `command` |
| | `context/narrow-tools`, `trim-tool-output`, `repair-think-tags`; `delegate/collapse-handoffs` | payload filter, `tool_result`, `message_end`, `context` |
| mixed (5) | `check/code-quality`, `nudge/empty-turn` | `agent_before_settle` continue; the fix is a message |
| | `guard/turn-cap`, `tool/keep-a-plan`, `workflow/spec-driven-flow` | block, then ask in prose |
| affordance (1) | `tool/lookup-library-docs` | `registerTool` |

## What Pi lets a handler change

| Hook | Can | Note |
| --- | --- | --- |
| `tool_call` | block with a reason, add `terminate`, mutate `event.input` | First block wins; input is not re-validated. |
| `tool_result` | replace `content`, `isError` | Chained across handlers. |
| `message_end` | replace the finished message | Before tool calls are extracted, so it can add or fix a call. |
| `context`, `before_provider_request` | replace messages / the payload | Every request. |
| `agent_before_settle`, `turn_end` | set `continue`, return `entries` | A returned `entries` **replaces** the shared list. |
| `registerTool` (same name) | replace a built-in | `prepareArguments`, `executionMode: "sequential"`, `terminate`. |
| `createBashToolDefinition` + `BashOperations` | own every command | `spawnHook` rewrites command, cwd, env per call. |
| `pi.exec(cmd, args, {timeout})`, `ctx.abort`, `setThinkingLevel`, `appendEntry` | bounded subprocess, hard stop, per-phase thinking, durable state | |

We use none of `terminate`, `prepareArguments`, `executionMode`, `spawnHook`, a replacement
`bash`, `pi.exec` with a timeout, `appendEntry` or `setThinkingLevel`.

## Two defects in the settle layer (read from code on `integration`)

- **Entries replaced, not appended.** `check/code-quality` (`mellum-quality.ts:110`) and
  `nudge/empty-turn` (`mellum-guards.ts:91`) each return `entries: [theirs]`. Loaded together,
  the later one overwrites the earlier one's message while both spend a re-dispatch. Fix:
  `[...event.entries, mine]`, with a test that loads two red gates.
- **No timeout on checks.** `code-quality` runs `uvx ruff` through `spawnSync` with no timeout
  (`mellum-quality.ts:136`); the ladder's `mellum-verify` runs pytest through `execSync` with none
  (`mellum-verify.ts:75`). A check that hangs hangs settle. Fix: a group-killed timeout, reported
  as red.

## Top five guarantees (ranked; all unmeasured)

1. **Never settle on code that does not compile or import.** On `tool_result` for a `.py`
   `write`/`edit`, compile it and return the error with `isError: true`; at settle, import each
   module the session wrote, under a timeout. Targets the quote-pairing `SyntaxError` and wrong
   imports that zero a session. Agnostic: keys on the file extension and the model's own writes.
2. **Fix the settle layer first** (the two defects above), before stacking more gates on it.
3. **A mediated test for Easy.** No hook can see a spec reading (an id on the model, a title
   block in a template). An external, frozen test at settle can. No suite on `integration` has a
   `mediated/` test yet; the unit and Medium's tests exist only on the old branch.
4. **An idle-bounded `bash`** that, after N s of silence, returns the output so far and the pid
   without killing the process, and answers a repeated launch from the live process. Targets the
   relaunch loop and the foreground-server hang. F.1 saw the hang again: the `worker` session sat
   on `uvicorn --reload` from request 36 to its 900 s deadline, a pure budget loss.
5. **Fix `PATH` once with `spawnHook`**: the workspace's `.venv/bin` first, so a bare `python`
   or `pytest` resolves. Can ship with #4.

Below the five, for budget: `terminate` on `guard/turn-cap` (a real stop, not a request); a
`tool_result` handler that shows the lines around a failed `edit` (edit-miss loops); per-phase
`setThinkingLevel`. Thinking is on today; do not turn it off for repairs without a rung arm (the
[2026-10-20 v7 ablation](2026-10-20-v7-ablation.md) found fixed-high thinking fastest, 163 s with no re-dispatch, on rung 9).

## What would falsify this

- Compile-on-write fires and the same session still settles on a `SyntaxError`.
- An import gate whose `ImportError` the model "fixes" by deleting the code that needs it.
- Two red settle gates in a fake-provider test both delivering their message (defect 1 wrong).
- An idle-bounded `bash` producing as many launches per session as today.

## Risks

- Pi line numbers are from the old branch's reading of `v1.4.0` source; no hook was executed.
- A replacement `bash` or `spawnHook` changes every command and what "Vanilla Pi" means: each
  ships as its own unit behind `--remedy`, never in the worker.
- Settle gates cost wall time per phase; on a short deadline that can cost a session.
