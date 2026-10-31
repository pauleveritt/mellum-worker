# Working with the extensions and the code

A walk through what happens to a change, from the file you edit to the number it earns on the
scoreboard. Read [`AGENTS.md`](../AGENTS.md) first; this traces the path those rules describe.

## The two kinds of code

Everything that changes how the worker behaves is one of two things.

- An **extension** lives in `extensions/mellum-*.ts`. It hooks Pi's events — `session_start`,
  `agent_before_settle` — and does its work there. `mellum-acceptance` derives a contract from
  the spec at `session_start`; `mellum-ncm` re-runs that contract when the worker tries to
  settle and sends it back while it is red. An extension is self-contained Node, so it loads
  with `-e extensions/mellum-ncm.ts` and needs no patch into Pi.
- A **remedy unit** lives in `remedies/<category>/<verb-noun>.ts`. It is a thin, named wrapper
  the course can switch on one at a time — `guard/cap-turns`, `tool/background-long-commands`.
  Most re-export an extension unchanged; the name is what a lesson teaches.

You will reach for a remedy unit when a lesson adds exactly one behaviour, and for an extension
when you are building the behaviour itself.

## How a run moves

A run starts at `learn/code/harness.py run`. You name a suite (`--suite easy`), an arm, and any
units to stack on top:

```bash
uv run python learn/code/harness.py run --suite easy --suites-dir learn/code/suites \
  --arm bare --remedy tool/background-long-commands \
  --extension extensions/mellum-acceptance.ts --extension extensions/mellum-ncm.ts \
  --grade --repeat 3 --deadline 1800 --stall 120 --profile <profile> --runs-dir runs/<name>
```

The harness copies the suite's `base/` into a fresh workspace, launches Pi with the arm's
settings and your units, and watches. If a tool call goes silent past `--stall`, the session
will be ended as stalled. When the child exits, the harness runs the hidden grader itself — the
worker's own "done" is never trusted — and writes `run.json`: the config it ran (`arm`,
`model`, `remedies`, `extensions` with their `sha256`), and what happened (`passed`, `turns`,
`tool_calls`, `wall`, `missing_checks`). That file is the unit of evidence everything downstream
reads.

## The loop you actually work in

A change to an extension is made test-first, and proven by mutation.

1. **Write the test first.** The Node suite is `npm test`; a new test is shown to fail before
   the code that passes it. `tests/mellum-acceptance.test.mjs` pins what the contract derives
   from a spec fixture.
2. **Make it pass, then prove it is complete.** A contract check is only real if it goes green
   on a correct build and red on the known miss. Regenerate the contract against the
   `known-good` fixture — it must pass — and against a workspace with the fault — it must fail
   on exactly that line. A check that cannot go red buys nothing.
3. **Measure a screen.** Run the suite at `--repeat 3` on the real model and read the pass rate
   with the turns and wall beside it. A pass is not the finish line: a shorter run, fewer turns,
   is the better pass, so judge the stack by its turns and wall, not pass-rate alone.
4. **Record it.** Point the scoreboard at the run dir and it writes one entry file:

   ```bash
   uv run python learn/code/scoreboard.py record runs/<name>/<rep> --model <model-id>
   ```

Because the entry carries the extensions' `sha256`, an edit you make is a new **version** of the
same stack. If it is faster, it will show as a new record that beats the old one rather than
blending into it — which is how you see an improvement land.

## Two rules that never bend

- **The hidden grader is the oracle; your contract is a proxy.** Read the grader to diagnose a
  miss, never to encode its answers. A fix is general test discipline with no suite-specific
  route, table or value — or it is cheating the eval.
- **A measured setting is frozen without evidence.** The prompt, the templates, the guards and
  the sampling do not change on a hunch; they change on a recorded run. A setting the shipped
  worker does not use is a harness finding, not a claim about the worker.

## Carrying learnings forward

`learn/code/improve.py` is the opt-in loop that tries to make later runs better: after each rep
it folds what the records teach into a carried `## Mellum` section, and the shipped worker reads
that section as facts on the next rep. It runs against a temp copy of the suite and its own
records file, so it never touches a measurement. Whether the carried facts actually pull the
turn-count down across iterations is the thing it measures — and the thing the scoreboard will
show.

Now pick a remedy and run the before line — the rest is reading the number it earns.
