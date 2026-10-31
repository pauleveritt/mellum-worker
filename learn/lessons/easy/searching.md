---
title: Searching
tier: easy
number: E4
time: 3 min read · 20 min to run
track: lessons
position: 4
prerequisites: [lessons/easy/looking-around]
authors: [Andre van Zuydam]
backends: [omlx]
---

# E4 · Searching

The grep and find tools let the model search a project, and a small model can aim them at the whole machine: a recursive search from the root crawls for minutes and hangs the run. One guard keeps its searches inside the workspace.

!!! abstract "Overview"

    **Questions**

    - What do `grep` and `find` give the model, and how does it misuse them?
    - How do I keep a search inside the project?

    **Objectives**

    - Recognise a machine-wide search in a trace: an absolute path outside the workspace.
    - Add `guard/stay-in-workspace` and see the search refused with a relative alternative.

![A small robot with a flashlight searching an enormous warehouse while its own small room sits behind it](../../assets/illustrations/searching.webp){ .illustration }

## Problem

**Badge:** `screen`

The tools: `grep` searches file contents, `find` lists files by name. Both take a path, and a small model sometimes gives them one far outside the project (`grep -rl pattern /Users /var /tmp`). The search walks the whole disk, returns nothing useful, and burns the session's time.

## Eval case

**Badge:** `conjecture`

**Before:** bare Pi with what the earlier Easy lessons added
(`guard/break-repeat-loops`). **After:** the same plus `guard/stay-in-workspace`. The
lesson's own challenge, a task built to provoke this failure, is not built
yet, so for now both run on Bronze.

## Evidence of the problem

**Badge:** `screen`

Recorded on the oMLX ladder: a worker ran `grep -rl pattern /Users /var /tmp …` and hung the run for minutes. Not seen in the nine bare sessions of 2026-10-29 on the vLLM host.

## Solution

**Badge:** `screen`

**Remedy unit:** `guard/stay-in-workspace`; apply it with `--remedy guard/stay-in-workspace`.

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

The guard reads every `bash` command that walks a tree (`find`, `rg`, `grep -r`, `ls -R`). If one names an absolute path outside the workspace, it is refused, with the relative form to use instead. Searches inside the workspace pass untouched.

```ts
const outside = absolutePathArgs(command).filter((p) => !isUnder(p));
if (outside.length) return { block: true, reason: `That searches outside your workspace … use relative paths` };
```

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. This page says FAIL → PASS only once its
challenge has shown it.

## Interpretation

The weakest badge is `conjecture`: the pathology is recorded, the fix is not measured on its own. The guard covers searches only. A write to an absolute path outside the workspace is not blocked yet; on 2026-10-29 one session wrote `app.py` into the repository it ran in, which is why a write-confining guard is planned.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy guard/break-repeat-loops --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy guard/break-repeat-loops,guard/stay-in-workspace --repeat 3 --grade
```

!!! success "Key points"

    - `grep` and `find` take a path, and a small model sometimes gives them the whole disk.
    - `guard/stay-in-workspace` refuses a search outside the project and shows the relative form.
    - It confines searches, not writes; writes outside the workspace still need their own guard.
