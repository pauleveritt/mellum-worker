---
title: Remedies
---

# Remedies you can try

![A small robot fitting a new part onto itself](../assets/illustrations/build-a-remedy.webp){ .illustration }

You do not need to read all of these. Start from a preset — `/remedy
preset:easy` switches on the whole Easy stack at once — run the tier, and reach
for a single unit only when the trace shows a problem the preset missed. Each
row is one problem and the unit that answers it; the last column is the
`/remedy` command that switches it on in a live Pi.

<!-- remedies:start -->

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Starts `python app.py` in the foreground and the session hangs until its deadline | `guard/block-foreground-server`: Blocks a foreground server start and shows the background form | screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy | `/remedy on guard/block-foreground-server` |
| Repeats the same call over and over (245 identical `ls -R` calls in one run) | `guard/break-repeat-loops`: Blocks a call made 5 times in a row with nothing changed in between | ladder: part of the guard set behind phase 2b's 15/15 | `/remedy on guard/break-repeat-loops` |
| Keeps calling tools with no end, because Pi has no turn cap | `guard/cap-turns`: Blocks every call after a budget (default 200) and asks for a summary | dormant in the worker; unmeasured | `/remedy on guard/cap-turns` |
| Rewrites a whole file to change a few lines (942 lines became 2) | `guard/refuse-whole-file-rewrite`: Blocks `write` to an existing file and asks for `edit` | recorded once; dormant in the worker (its column never went non-zero) | `/remedy on guard/refuse-whole-file-rewrite` |
| Searches the whole machine (`grep -rl x /Users /var`) and hangs the run | `guard/stay-in-workspace`: Blocks a recursive search that names a path outside the workspace | screen: recorded hangs; searches only, writes are not covered | `/remedy on guard/stay-in-workspace` |
| Ends a turn with no reply and no tool call, part-way through the task | `nudge/nudge-empty-turn`: Restates the completion fact and asks for one more turn, at most 3 times | ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2) | `/remedy on nudge/nudge-empty-turn` |
| Guesses how to run the tests instead of using the project's own command | `context/add-project-facts`: Appends the project facts (AGENTS.md `## Mellum`, test command) to user messages | screen: 3/3 against 2/3 on Easy (2026-10-29); a null in the page's record | `/remedy on context/add-project-facts` |
| Reaches for tools it uses badly (subagents, todo lists) instead of reading and editing | `context/narrow-tools`: Keeps read, grep, find, ls, bash, edit and write, plus tools your units register; drops the rest | part of the Baseline Worker; not measured on its own | `/remedy on context/narrow-tools` |
| The serving stack returns reasoning as `<think>` text, and the model is fed it back as things it said | `context/repair-think-tags`: Moves a leading `<think>…</think>` in a reply into a thinking block, sent back as reasoning; leaves a correctly served reply alone | LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0 | `/remedy on context/repair-think-tags` |
| Reads more than the context holds, so Pi compacts it and the model loses what it read first | `context/trim-tool-output`: Trims a read, bash, grep, find or ls result over 8,000 characters and says how to search for the rest | context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again | `/remedy on context/trim-tool-output` |
| A long, procedural system prompt the small model follows instead of the files | `context/use-short-prompt`: Replaces the system prompt with the 643-character prompt in prompts/mellum-worker.md | screen: 3/3 against 1/3 on Easy (2026-10-29), 3/9 against 3/9 earlier; not decided | `/remedy on context/use-short-prompt` |
| Invents its own file layout instead of the one the spec names (e.g. writes main.py, skips the named folders) | `prompt/name-the-layout`: Appends one line telling the model to take the file layout from the project's spec, not invent one | new unit; unmeasured | `/remedy on prompt/name-the-layout` |
| Runs a server or watcher in the foreground and the session waits forever | `tool/background-long-commands`: Rewrites a long-running bash command to run in the background and returns its startup output | unit-tested; not measured on the suites | `/remedy on tool/background-long-commands` |
| Loses track of a long task part-way through | `tool/keep-a-plan`: Keeps a TODO.md the model writes, follows and amends on failures | unit-tested; not measured on the suites | `/remedy on tool/keep-a-plan` |
| Guesses an API it never saw (a post-cutoff library, a redirect status) | `tool/lookup-library-docs`: Adds a lookup tool over the installed packages' signatures and docs | unit-tested; not measured on the suites | `/remedy on tool/lookup-library-docs` |
| Finishes with lint or type errors the grader counts as a fail | `check/check-code-quality`: Runs the quality checks before the model may finish | unit-tested; not measured on the suites | `/remedy on check/check-code-quality` |
| Builds a multi-phase app in one go and breaks earlier phases | `workflow/spec-driven-flow`: Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py) | flow runs 2026-10-29: Easy 4/4, Medium 18/18, Hard 30/34 (n = 1) | `/remedy on workflow/spec-driven-flow` |

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
