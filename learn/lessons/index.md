# Lessons

Each lesson takes one thing a small coding model gets wrong, measures it, and
shows what changes it. The lessons are grouped in three tiers that rise in
level, and every lesson stands on its own: [Getting started](../getting-started/index.md)
is the only thing you need first, unless a lesson's prerequisites say
otherwise.

![A small robot climbing three wide steps that rise from easy to hard](../assets/illustrations/lessons.webp){ .illustration }

<div class="grid cards" markdown>

-   **[Easy](easy/index.md)**

    ---

    One setting, one visible effect. You read the result in a table, and you
    can follow it from Getting started alone.

-   **[Medium](medium/index.md)**

    ---

    How the model spends its session: its thinking, its empty turns, the
    shape of the task it is handed. You will read a trace.

-   **[Hard](hard/index.md)**

    ---

    Orchestration and advanced concepts: who drives the model, how work is
    split, checked and re-dispatched.

</div>

The lessons' runs use the Bronze, Silver and Gold levels of
[The Challenge](../challenge/index.md). A lesson's tier says how far into the
material it goes, not which level it runs on.

New here? Start with [S0 · Start Here](start-here.md): one minute, no model
needed, and it shows you how every lesson works.

## Take the lessons in Pi

Every lesson also runs inside Pi, the harness it teaches. From your checkout
of this repository:

```bash
pi
```

The first time, type `/trust` and restart Pi, so it loads the project's
extensions. Then:

- `/lesson` picks a lesson (finished ones are ticked, the next one comes
  first, and Start Here comes first of all), and `/lesson E1` opens one. It shows the lesson's picture and walks
  you through each step; on the Eval case and Solution steps, `r` runs the
  before and after lines and tells you whether each session passed and why.
- `/remedy` switches remedy units on and off in your live session, so you can
  try one by hand: `/remedy on guard/break-repeat-loops`, `/remedy off …`,
  or `/remedy preset:easy`.

Pictures show in terminals that draw images (Kitty, Ghostty, WezTerm, iTerm2);
elsewhere you see their description.

## Pathologies and their remedies

Every remedy these lessons teach is a small unit you can switch on by itself.
The same list is on [The Challenge](../challenge/index.md), where you can
apply any of them to an attempt with the line in the last column.

<!-- remedies:start -->

| Pathology | Remedy unit | Lesson | Evidence | Apply it |
| --- | --- | --- | --- | --- |
| Starts `python app.py` in the foreground and the session hangs until its deadline | `guard/block-foreground-server`: Blocks a foreground server start and shows the background form | n/a | screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy | `--remedy guard/block-foreground-server` |
| Repeats the same call over and over (245 identical `ls -R` calls in one run) | `guard/break-repeat-loops`: Blocks a call made 5 times in a row with nothing changed in between | [E3](easy/looking-around.md) | ladder: part of the guard set behind phase 2b's 15/15 | `--remedy guard/break-repeat-loops` |
| Keeps calling tools with no end, because Pi has no turn cap | `guard/cap-turns`: Blocks every call after a budget (default 200) and asks for a summary | [E7](easy/know-when-to-stop.md) | dormant in the worker; unmeasured | `--remedy guard/cap-turns` |
| Rewrites a whole file to change a few lines (942 lines became 2) | `guard/refuse-whole-file-rewrite`: Blocks `write` to an existing file and asks for `edit` | [E5](easy/creating-files.md) | recorded once; dormant in the worker (its column never went non-zero) | `--remedy guard/refuse-whole-file-rewrite` |
| Searches the whole machine (`grep -rl x /Users /var`) and hangs the run | `guard/stay-in-workspace`: Blocks a recursive search that names a path outside the workspace | [E4](easy/searching.md) | screen: recorded hangs; searches only, writes are not covered | `--remedy guard/stay-in-workspace` |
| Ends a turn with no reply and no tool call, part-way through the task | `nudge/nudge-empty-turn`: Restates the completion fact and asks for one more turn, at most 3 times | [M3](medium/nudge-an-empty-turn.md) | ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2) | `--remedy nudge/nudge-empty-turn` |
| Guesses how to run the tests instead of using the project's own command | `context/add-project-facts`: Appends the project facts (AGENTS.md `## Mellum`, test command) to user messages | [M1](medium/tell-it-how-to-test.md) | screen: 3/3 against 2/3 on Bronze (2026-10-29); a null in the page's record | `--remedy context/add-project-facts` |
| Reaches for tools it uses badly (subagents, todo lists) instead of reading and editing | `context/narrow-tools`: Keeps read, grep, find, ls, bash, edit and write, plus tools your units register; drops the rest | [E6](easy/too-many-tools.md) | part of the Baseline Worker; not measured on its own | `--remedy context/narrow-tools` |
| The serving stack returns reasoning as `<think>` text, and the model is fed it back as things it said | `context/repair-think-tags`: Moves a leading `<think>…</think>` in a reply into a thinking block, sent back as reasoning; leaves a correctly served reply alone | [E1](easy/reasoning-as-text.md) | LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0 | `--remedy context/repair-think-tags` |
| Reads more than the context holds, so Pi compacts it and the model loses what it read first | `context/trim-tool-output`: Trims a read, bash, grep, find or ls result over 8,000 characters and says how to search for the rest | [E2](easy/context-overflow.md) | context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again | `--remedy context/trim-tool-output` |
| A long, procedural system prompt the small model follows instead of the files | `context/use-short-prompt`: Replaces the system prompt with the 643-character prompt in prompts/mellum-worker.md | [M2](medium/a-short-prompt.md) | screen: 3/3 against 1/3 on Bronze (2026-10-29), 3/9 against 3/9 earlier; not decided | `--remedy context/use-short-prompt` |
| Runs a server or watcher in the foreground and the session waits forever | `tool/background-long-commands`: Rewrites a long-running bash command to run in the background and returns its startup output | [M4](medium/run-long-commands-safely.md) | unit-tested; not measured on the suites | `--remedy tool/background-long-commands` |
| Loses track of a long task part-way through | `tool/keep-a-plan`: Keeps a TODO.md the model writes, follows and amends on failures | [M7](medium/keep-a-plan.md) | unit-tested; not measured on the suites | `--remedy tool/keep-a-plan` |
| Guesses an API it never saw (a post-cutoff library, a redirect status) | `tool/lookup-library-docs`: Adds a lookup tool over the installed packages' signatures and docs | [M5](medium/look-it-up.md) | unit-tested; not measured on the suites | `--remedy tool/lookup-library-docs` |
| Finishes with lint or type errors the grader counts as a fail | `check/check-code-quality`: Runs the quality checks before the model may finish | [M6](medium/check-before-finishing.md) | unit-tested; not measured on the suites | `--remedy check/check-code-quality` |
| Builds a multi-phase app in one go and breaks earlier phases | `workflow/spec-driven-flow`: Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py) | [H1](hard/plan-examine-code.md) | flow runs 2026-10-29: Bronze 4/4, Silver 18/18, Gold 30/34 (n = 1) | `learn/code/flow_run.py` |

<!-- remedies:end -->

## How every lesson reads

Every lesson page has the same shape, so you know where to look:

1. **Two sentences:** the problem and the solution.
2. **Overview:** the questions the lesson answers and what you will be able to
   do after it.
3. **Six steps:** Problem, Eval case, Evidence of the problem, Solution,
   Validation, Interpretation. Each step carries its own evidence badge
   ([what the badges mean](../about/evidence.md#badges)).
4. **Run it yourself:** the command that reproduces the lesson's arms, or a
   plain statement that it has none yet.
5. **Key points:** what to take away, never stronger than the evidence.
