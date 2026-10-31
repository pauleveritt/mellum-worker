---
title: The Challenge
---

# The Challenge

You have run a small model, built a harness and read what goes wrong. Now
prove it: point your setup at the same three projects every lesson is measured
on, and see how far it gets.

![A small robot on a winners' podium with bronze, silver and gold medals](../assets/illustrations/challenge.webp){ .illustration }

## The three levels

Each level is the same AgentClinic web app at a bigger scope. A hidden grader
runs after your session ends, so the model cannot see or edit what it is
judged on.

<div class="grid cards" markdown>

-   **Bronze**

    ---

    One prompt: build the home page. **4 hidden checks.** A good first
    target: a setup that holds together passes it in minutes.

-   **Silver**

    ---

    Four prompts, one per phase of a growing app. **18 hidden checks.** The
    model has to keep earlier phases working while it adds new ones.

-   **Gold**

    ---

    Eleven prompts: an archive, an audit trail, a SQLite database and
    reports. **34 hidden checks.** No setup measured here has passed it yet.

</div>

## The score to beat

The suite baseline is the reference: Pi with no remedies, three sessions per
level on llama.cpp ([Start Here](../lessons/start-here.md#reading-a-real-failure)
shows what it gets wrong), with the same Mellum model you set up in
[Getting Started](../getting-started/index.md). The last row is the replicable
baseline: the same model at full precision on a rented GPU, rebuilt with
`scripts/baseline/baseline.py`.

| Setup | Bronze | Silver | Gold |
| --- | --- | --- | --- |
| Pi on its own | 0/3 | 0/3 | 0/3 |
| The Baseline Worker | 1/3 | 2/3 | 0/3 |
| Pi on its own, BF16 on vLLM (the replicable baseline) | 1/3 | 1/3 | 0/3 |

A pass means every hidden check passed. Anything less is a fail, and the
record tells you which checks were missing and why.

## Attempt it

You need the [Getting Started](../getting-started/index.md) setup: a local
model, Pi, and the suites. You do not need the lessons; they are a reference
for when a run fails in a way you do not understand.

**Straight from Getting Started**, run a level three times with bare Pi:

```bash
uv run python learn/code/harness.py run --suite easy --repeat 3 --grade
```

Bronze is `--suite easy`, Silver `--suite medium` and Gold `--suite hard`.
Each session gets a fresh copy of the project; the summary line says how many
of the three passed, and each session's `run.json` lists the checks it
missed. Then add remedies, one line at a time, from the list below, or a
whole tier at once:

```bash
uv run python learn/code/harness.py run --suite medium --remedy preset:easy --repeat 3 --grade
```

**After the lessons**, start from everything the course ships, and add your
own extension on top:

```bash
uv run python learn/code/harness.py run --suite hard --remedy preset:hard --repeat 3 --grade
uv run python learn/code/harness.py run --suite hard --remedy preset:hard --extension path/to/yours.ts --repeat 3 --grade
```

Hard's orchestration (plan, examine, code, frozen gates) runs through
`learn/code/flow_run.py --suite hard` instead; the
[Hard lessons](../lessons/hard/index.md) show how.

Change one thing at a time, run the same level again, and compare. That is
exactly how every [lesson](../lessons/index.md) is built.

## Remedies you can try

Each row is one problem a small model has and one remedy unit for it. Add the
line in the last column to your attempt to switch that remedy on; combine
several with commas (`--remedy guard/break-repeat-loops,nudge/nudge-empty-turn`),
or use the whole worker with `--remedy preset:baseline-worker`. Start from the
lesson that teaches a remedy if you want to know why it works.

<!-- remedies:start -->

| Pathology | Remedy unit | Lesson | Evidence | Apply it |
| --- | --- | --- | --- | --- |
| Starts `python app.py` in the foreground and the session hangs until its deadline | `guard/block-foreground-server`: Blocks a foreground server start and shows the background form | n/a | screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy | `--remedy guard/block-foreground-server` |
| Repeats the same call over and over (245 identical `ls -R` calls in one run) | `guard/break-repeat-loops`: Blocks a call made 5 times in a row with nothing changed in between | [E3](../lessons/easy/looking-around.md) | ladder: part of the guard set behind phase 2b's 15/15 | `--remedy guard/break-repeat-loops` |
| Keeps calling tools with no end, because Pi has no turn cap | `guard/cap-turns`: Blocks every call after a budget (default 200) and asks for a summary | [E7](../lessons/easy/know-when-to-stop.md) | dormant in the worker; unmeasured | `--remedy guard/cap-turns` |
| Rewrites a whole file to change a few lines (942 lines became 2) | `guard/refuse-whole-file-rewrite`: Blocks `write` to an existing file and asks for `edit` | [E5](../lessons/easy/creating-files.md) | recorded once; dormant in the worker (its column never went non-zero) | `--remedy guard/refuse-whole-file-rewrite` |
| Searches the whole machine (`grep -rl x /Users /var`) and hangs the run | `guard/stay-in-workspace`: Blocks a recursive search that names a path outside the workspace | [E4](../lessons/easy/searching.md) | screen: recorded hangs; searches only, writes are not covered | `--remedy guard/stay-in-workspace` |
| Ends a turn with no reply and no tool call, part-way through the task | `nudge/nudge-empty-turn`: Restates the completion fact and asks for one more turn, at most 3 times | [M3](../lessons/medium/nudge-an-empty-turn.md) | ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2) | `--remedy nudge/nudge-empty-turn` |
| Guesses how to run the tests instead of using the project's own command | `context/add-project-facts`: Appends the project facts (AGENTS.md `## Mellum`, test command) to user messages | [M1](../lessons/medium/tell-it-how-to-test.md) | screen: 3/3 against 2/3 on Bronze (2026-10-29); a null in the page's record | `--remedy context/add-project-facts` |
| Reaches for tools it uses badly (subagents, todo lists) instead of reading and editing | `context/narrow-tools`: Keeps read, grep, find, ls, bash, edit and write, plus tools your units register; drops the rest | [E6](../lessons/easy/too-many-tools.md) | part of the Baseline Worker; not measured on its own | `--remedy context/narrow-tools` |
| The serving stack returns reasoning as `<think>` text, and the model is fed it back as things it said | `context/repair-think-tags`: Moves a leading `<think>…</think>` in a reply into a thinking block, sent back as reasoning; leaves a correctly served reply alone | [E1](../lessons/easy/reasoning-as-text.md) | LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0 | `--remedy context/repair-think-tags` |
| Reads more than the context holds, so Pi compacts it and the model loses what it read first | `context/trim-tool-output`: Trims a read, bash, grep, find or ls result over 8,000 characters and says how to search for the rest | [E2](../lessons/easy/context-overflow.md) | context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again | `--remedy context/trim-tool-output` |
| A long, procedural system prompt the small model follows instead of the files | `context/use-short-prompt`: Replaces the system prompt with the 643-character prompt in prompts/mellum-worker.md | [M2](../lessons/medium/a-short-prompt.md) | screen: 3/3 against 1/3 on Bronze (2026-10-29), 3/9 against 3/9 earlier; not decided | `--remedy context/use-short-prompt` |
| Runs a server or watcher in the foreground and the session waits forever | `tool/background-long-commands`: Rewrites a long-running bash command to run in the background and returns its startup output | [M4](../lessons/medium/run-long-commands-safely.md) | unit-tested; not measured on the suites | `--remedy tool/background-long-commands` |
| Loses track of a long task part-way through | `tool/keep-a-plan`: Keeps a TODO.md the model writes, follows and amends on failures | [M7](../lessons/medium/keep-a-plan.md) | unit-tested; not measured on the suites | `--remedy tool/keep-a-plan` |
| Guesses an API it never saw (a post-cutoff library, a redirect status) | `tool/lookup-library-docs`: Adds a lookup tool over the installed packages' signatures and docs | [M5](../lessons/medium/look-it-up.md) | unit-tested; not measured on the suites | `--remedy tool/lookup-library-docs` |
| Finishes with lint or type errors the grader counts as a fail | `check/check-code-quality`: Runs the quality checks before the model may finish | [M6](../lessons/medium/check-before-finishing.md) | unit-tested; not measured on the suites | `--remedy check/check-code-quality` |
| Builds a multi-phase app in one go and breaks earlier phases | `workflow/spec-driven-flow`: Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py) | [H1](../lessons/hard/plan-examine-code.md) | flow runs 2026-10-29: Bronze 4/4, Silver 18/18, Gold 30/34 (n = 1) | `learn/code/flow_run.py` |

<!-- remedies:end -->

The evidence column is honest: several remedies are screens or nulls on the
current host. Finding out which combination passes is the point.

## Build your own

When no remedy in the list fixes what you see in the trace, write one:

1. Copy the smallest unit, `remedies/guard/break-repeat-loops.ts`, as a
   template. A unit installs one behaviour on one of Pi's hooks and exports a
   `meta` record: the pathology, what it does, its evidence.
2. Load it into an attempt with `--extension path/to/your-unit.ts`, alone or
   on top of other remedies, and run a level three times.
3. Submit a pull request with your unit, the attempt's `run.json` files and a
   short note on the problem it fixes and what the trace showed.

A submitted remedy that measurably helps is the start of a new lesson.

## Tips

- Start with Bronze. If it does not pass, the problem is in the setup, not the
  model's ambition; [Troubleshooting](../getting-started/troubleshoot.md)
  covers the usual causes.
- Read the trace, not only the score: [Pathologies](../pathologies.md) names
  the ways a small model goes wrong, and most failed sessions show one of
  them.
- Compare like with like: the same level, the same number of sessions, one
  change at a time.
