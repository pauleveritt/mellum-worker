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

### Guards

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Starts a foreground server and hangs to the deadline | `guard/foreground-server`: Blocks a foreground server start and shows the background form | screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy | `/remedy on guard/foreground-server` |
| Searches the whole machine and hangs the run | `guard/outside-workspace`: Blocks a recursive search outside the workspace | screen: recorded hangs; searches only, writes are not covered | `/remedy on guard/outside-workspace` |
| Repeats the same call with nothing changed | `guard/repeat-loops`: Blocks a call made 5 times in a row unchanged | ladder: part of the guard set behind phase 2b's 15/15 | `/remedy on guard/repeat-loops` |
| Calls tools with no end | `guard/turn-cap`: Blocks calls past a budget (default 200) and asks for a summary | dormant in the worker; unmeasured | `/remedy on guard/turn-cap` |
| Rewrites a whole file to change a few lines | `guard/whole-file-rewrite`: Blocks `write` to an existing file and asks for `edit` | recorded once; dormant in the worker (its column never went non-zero) | `/remedy on guard/whole-file-rewrite` |

### Nudges

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Ends a turn empty, part-way through the task | `nudge/empty-turn`: Restates the goal and asks for one more turn (at most 3) | ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2) | `/remedy on nudge/empty-turn` |

### Context

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Reaches for tools it uses badly instead of reading and editing | `context/narrow-tools`: Keeps the seven core tools; drops the rest | part of the Baseline Worker; not measured on its own | `/remedy on context/narrow-tools` |
| Reasoning comes back as `<think>` text and is fed back as speech | `context/repair-think-tags`: Turns a leading `<think>` reply back into a thinking block | LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0 | `/remedy on context/repair-think-tags` |
| Reads more than the context holds, then loses it to compaction | `context/trim-tool-output`: Trims a tool result over 8,000 chars and says how to get the rest | context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again | `/remedy on context/trim-tool-output` |
| Follows a long system prompt instead of the files | `context/use-short-prompt`: Swaps in the 643-character worker prompt | screen: 3/3 against 1/3 on Easy (2026-10-29), 3/9 against 3/9 earlier; not decided | `/remedy on context/use-short-prompt` |

### Prompts

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Builds each file to completion in turn, so the layout drifts and earlier parts break | `prompt/concept-sketch`: Sketch every file first (signatures and stubs), then fill the bodies one at a time | new unit (prose v1); unmeasured — a lead, see the next-concept research note | `/remedy on prompt/concept-sketch` |
| Invents its own file layout instead of the one the spec names | `prompt/name-the-layout`: Injects the spec-layout instruction once per task | task-scoped delivery verified locally; coding effect unmeasured | `/remedy on prompt/name-the-layout` |
| Works without a focused, careful developer frame (ships typos, declares done unchecked) | `prompt/python-developer`: Prepends a meticulous experienced-Python-developer, spec-driven role to the system prompt | theory; unmeasured (easy-ladder, 2026-11-02) | `/remedy on prompt/python-developer` |
| Declares done with a spec requirement unimplemented or unverified | `prompt/verify-the-spec`: Injects the requirement-and-test verification instruction once per task | new unit; unmeasured (easy-ladder, 2026-11-02) | `/remedy on prompt/verify-the-spec` |

### Tools

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Runs a server in the foreground and waits forever | `tool/background-long-commands`: Reruns a long command in the background and returns its startup output | unit-tested; not measured on the suites | `/remedy on tool/background-long-commands` |
| Loses track of a long task | `tool/keep-a-plan`: Keeps a TODO.md it writes, follows and amends | unit-tested; not measured on the suites | `/remedy on tool/keep-a-plan` |
| Guesses an API it never saw | `tool/lookup-library-docs`: Adds a lookup over the installed packages' docs | unit-tested; not measured on the suites | `/remedy on tool/lookup-library-docs` |

### Checks

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Finishes with lint or type errors | `check/code-quality`: Runs the quality checks before finishing | unit-tested; not measured on the suites | `/remedy on check/code-quality` |

### Workflows

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Builds a multi-phase app in one go and breaks earlier phases | `workflow/spec-driven-flow`: Adds a plan with frozen per-phase gates and checkpoints | flow runs 2026-10-29: Easy 4/4, Medium 18/18, Hard 30/34 (n = 1) | `/remedy on workflow/spec-driven-flow` |

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
