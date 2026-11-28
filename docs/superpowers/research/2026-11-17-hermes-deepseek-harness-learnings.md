# What Hermes Agent and DeepSeek Harness do that we don't (2026-11-17)

**What is measured.** Nothing here was run against Mellum. Every mechanism below
was read from source: Hermes Agent v0.23.1 (Python, `~/.hermes/hermes-agent`)
and DeepSeek Harness 0.2.2-rc.1 (Node, its packages read out of the desktop
app's bundle). File and line references are to those trees. The one Mellum fact
quoted is the 2026-11-16 Easy hang: a backgrounded `uvicorn`, then
`tail -f /tmp/uvicorn.log`, held to the 600 s deadline.

**What is conjecture.** Every "for us" line is a theory. Each needs a unit,
a test shown red first, and an n=3 screen on the tier it targets before it
counts as a lesson.

## The shape of both harnesses

- **Both are built from small, separately switchable pieces, like our
  remedies.** DeepSeek Harness has about 330 plugin packages. Each README has a
  fixed section per model-facing effect: "What the model sees", "Token effect"
  and "KV Cache effect".
  *For us:* our `UnitMeta` records pathology, does, lesson and evidence. Adding
  "what the model sees" (the exact injected text) and its token and cache cost
  would make a unit's prefill price readable before a screen.
- **Both converge on the same answers for hangs, loops and verification.** Two
  independent teams landing on one design is a stronger lead than either alone.

## 1. Commands that never return

- **Time-based, not pattern-based.**
  - DeepSeek Harness gives every bash command a default 120 s timeout, capped
    at 600 s (`dsh-bash-local`).
  - A command that outlives its timeout isn't killed. It keeps running as a
    tracked job, and the call returns
    `[still running after <ms>ms; moved to background job <id>]` with its output
    so far (`dsh-tool-bash`, `promoteOnTimeout: true`).
  - Hermes does the same at 180 s by default and 600 s at most
    (`tools/terminal_tool.py:78,854`). It can also adopt a running foreground
    command as a background session.
- **Pi has no default.** Pi's `bash` timeout is optional, and it's an idle
  timeout: any output re-arms it (`pi/packages/coding-agent/src/core/tools/bash.ts:45`).
  So a `tail -f` on a log that keeps writing never times out, even when the
  model sets one.
- **Our units match command names.** `guard/foreground-server`,
  `guard/no-live-server` and `tool/background-long-commands` all key on server
  launchers. None of them catches `tail -f`, `watch` or `less`.
- *For us (the lead):* a `tool` unit that gives every bash call a wall-clock
  default and, past it, returns the output so far plus a job id instead of
  hanging. It's generic: no command list.
- **Pager and colour defaults.**
  - DeepSeek sets `NO_COLOR=1 TERM=dumb PAGER=cat GIT_PAGER=cat` on every
    command.
  - Hermes sets `PAGER` and `GIT_PAGER` to `cat` and strips ANSI from spilled
    output (`tools/process_registry.py:1169`).
  - *For us:* a cheap, agnostic env default, so a pager can never hang a call.

## 2. Servers: managed, not banned

- **Hermes runs servers through `background=true` and a `process_manage` tool**
  (list, poll, log, wait, kill). A watch pattern notifies on a matching line,
  rate-limited to one per 15 s and at most 8 in total.
- **It warns rather than blocks.** A foreground server or watch command gets
  "appears to start a long-lived server/watch process. Run it with
  background=true, verify readiness…, then execute tests in a separate command"
  (`tools/terminal_tool_guards.py:117`).
- *For us:* we ban servers (`no-live-server`), because a forked server
  disagreed with the in-process test client and fed a curl spiral on Medium.
  "Manage" against "ban" is an A/B worth one screen, not a switch.

## 3. Repeated calls: advise first, block late

- **DeepSeek only advises.** It reminds on the 3rd, 5th and 8th identical call,
  and never blocks. A new user message resets the count
  (`dsh-repeat-tool-reminder`).
- **Hermes advises and then escalates.**
  - The key is (tool, arguments, **result**), so a re-run that returns
    something new isn't a loop. It notices on the 3rd.
  - It also catches **cycles of period 2 to 4**, like A, B, A, B. A plain
    streak count misses these, because every alternation resets it
    (`agent/tool_guardrails.py:39,46`).
  - Blocks come later (exact failure at 5, same-tool failure at 8), and by
    default only when unattended.
- **Ours blocks at 5 identical calls, keyed on tool plus arguments**
  (`createLoopBreaker`, window 20).
- *For us:*
  - Key on the result too.
  - Detect short cycles.
  - Try an advisory reminder at 3 ahead of the block at 5.
- **Hermes stubs repeated reads.** A `read_file` of an unchanged region returns
  an "unchanged" stub, and blocks after repeated re-reads
  (`tools/file_tools.py:501-520`).
  *For us:* this saves prefill, our measured cost driver on Medium.

## 4. Settling and verification

- **Hermes `verify_on_stop`** (off by default, at most 2 nudges): if code was
  edited and there's no passing test evidence, it says "Run the relevant
  verification command now (`…`), read any failure, repair the code"
  (`agent/verification_stop.py:203`). The commands are auto-detected from the
  project.
- **Hermes `/goal`:** a judge model decides after each turn whether the goal is
  met, up to 20 turns. Optional shell "quality gates" must pass before it can
  declare done (`hermes_cli/goals.py`).
- **DeepSeek's goal round driver** re-prompts toward the objective while idle,
  within a round budget, and records a blocker when the budget runs out.
- **Where we stand:** our `mellum-verify` gate is the stricter version of
  this: an external, frozen acceptance test, not the agent's own tests or a
  judge.
- *For us:* both harnesses confirm settling is the harness's job. The
  difference worth keeping is that ours checks against the spec, not against
  the worker's own work.

## 5. Empty turns

- **Hermes has a ladder.** First one nudge ("You just executed tool calls but
  returned an empty response. Please process the tool results above and
  continue"), then up to 2 thinking-only prefills, then a small retry budget
  (`agent/turn_empty_response.py`).
- *For us:* `nudge/empty-turn` is a single step. A second rung is a theory.

## 6. Tool output and a small context

- **Both cut output to a head plus a tail, with a path to the full text.**
  - Hermes: 50,000 chars, 40% of it head.
  - DeepSeek: a token budget (`dsh-spill-policy`).
- **Hermes never spills `read_file`, to avoid a read-then-spill loop.**
- **Both prune old results before summarising, with no model call.**
  DeepSeek's `dsh-compaction-tool-result-pruner` keeps the head and tail of an
  old result. Hermes removes byte-identical duplicates.
- *For us:* `context/trim-tool-output` exists. The "never spill a read"
  exception and dropping duplicates in old history are untested ideas.

## 7. Edits

- **Both enforce read-before-write.**
  - A write to an existing file is refused unless the file was read and is
    unchanged since.
  - DeepSeek rejects a mutation when the file changed since the read, and
    tells the model to re-read (`dsh-fs-observation-policy`).
  - Hermes refuses `write_file` on an unread file, and nudges a near-identical
    whole-file rewrite towards `patch`.
- **Hermes `patch` tolerates whitespace and indentation drift**
  (`tools/fuzzy_match.py`, 9 matching strategies). That's a direct fix for
  small-model edit misses.
- **Hermes's prompt:** "If the same region fails twice, rewrite… with
  `write_file`", and "stop after about three attempts on the same file".
- *For us:* `guard/whole-file-rewrite` covers part of this. A fuzzy edit
  matcher is a `tool` unit nobody has tried.

## 8. Model-specific settings

- **Neither keys on model size.** Hermes gates prompt blocks by model-family
  name (`agent/prompt_builder.py:362,376`). A model named "mellum" gets neither
  its tool-use nor its execution-guidance block by default.
- **Hermes has a narrowed coding tool set** (`coding_context: focus`).
- *For us:* when we run Hermes as a comparison, list those blocks explicitly,
  or we'd be measuring a harness with half its prompt switched off.

## Ranked leads (all unmeasured)

1. **A bash wall-clock default that promotes to a background job.** It targets
   the only Easy hang we've seen, both harnesses do it, and it needs no command
   list.
2. **Pager and colour env defaults.** Near-zero cost, no measured failure yet.
3. **A loop key that includes the result, with cycle detection and an advisory
   rung at 3.**
4. **Repeated-read stubs.** Aimed at prefill cost on Medium.
5. **A cross-harness baseline:** Easy and Medium with Hermes driving Mellum,
   and DeepSeek Harness headless through its `pi-ai` route. This tells us which
   failures are Pi's.

## What would falsify this / risks

- **Lead 1** is wrong if an Easy or Medium screen with it shows no fewer
  deadline hangs than without. With one hang in 9 Easy reps, n=3 can't show
  that. It needs a larger n, or a fixture that reproduces the hang.
- **Promoting to background could feed the server spiral** that
  `no-live-server` exists to stop. The unit must compose with that guard, not
  replace it.
- **The other harnesses tune for large hosted models.** A threshold that suits
  them (Hermes noticing at 3) may be wrong for a 12B model. Treat their numbers
  as starting points, not settings.
- **Source reading can miss runtime behaviour**, such as config overrides or
  features switched off in the shipped profile. Hermes `verify_on_stop` is off
  by default, and DeepSeek's auto-review ships off.
