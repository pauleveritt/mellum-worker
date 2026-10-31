---
title: Check Before Finishing
tier: medium
number: M6
time: 3 min read · 20 min to run
track: lessons
position: 6
prerequisites: [lessons/medium/look-it-up]
authors: [Andre van Zuydam]
backends: [omlx]
---

# M6 · Check Before Finishing

A small model can declare itself done over code with real errors in it: a
function defined twice, a name left undefined after a rename. One unit runs
the checks at the finish and hands back what they found.

!!! abstract "Overview"

    **Questions**

    - What errors does a model leave behind that nothing flags while it writes?
    - How can the finish itself catch them?

    **Objectives**

    - Recognise the silent errors: a shadowed definition, an undefined name, an unused import.
    - Add `check/check-code-quality` and read the message it sends at the finish.

![A small robot with a magnifying glass checking a finished page beside a checklist with a few boxes still open](../../assets/illustrations/check-before-finishing.webp){ .illustration }

## Problem

**Badge:** `conjecture`

The model re-emits a whole function instead of editing it, so a second `def`
shadows the first; or it renames something and strands the old name; or it
leaves an import unused. None of these fails while it writes, and it declares
done. The grader runs `ruff`, and counts them.

## Eval case

**Badge:** `conjecture`

**Before:** `--remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands,tool/lookup-library-docs`.
**After:** the same plus `check/check-code-quality`. The lesson's own
challenge, a task that tempts a rewrite over an edit, is not built yet, so for
now both run on Bronze.

## Evidence of the problem

**Badge:** `conjecture`

The extension's notes record the shapes (pyflakes `F811`, `F821`, `F401`),
and the suites' grader includes `ruff`. No count on the suites says how often
a session fails on them alone.

## Solution

**Badge:** `conjecture`

**Remedy unit:** `check/check-code-quality`; apply it with `--remedy check/check-code-quality`.

**Lesson check:** not built yet. A small challenge of this lesson's own, failing without the remedy and passing with it, is planned; until then the evidence below is the suites'.

When the model tries to finish, the unit runs `ruff check --select F,E9` over
the workspace, skipping the tests. If real errors remain it lists each one and
asks the model to fix them, at most twice. `F,E9` is pyflakes plus syntax:
real errors only, never style, so a working solution is never held back on
cosmetics. If `ruff` cannot run, the unit stays silent. The message has this shape (an
illustration, not a recorded session):

```text
[mellum-quality] Before you finish: ruff found real errors in your own
changes (ruff --select F,E9). Fix each one, then finish:
  app.py:42:5 F811 Redefinition of unused `create_complaint` from line 18
```

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. The unit is unit-tested but has no
before-and-after record on the suites. This page says FAIL → PASS only once
its challenge has shown it.

## Interpretation

The weakest badge is `conjecture`. The check leans on `ruff` because a
hand-rolled "same name twice" scan would flag legitimate redefinitions such as
`@overload` and a property's setter, which `F811` already gets right. Whether
two nudges are enough for a small model to clean up is what the challenge has
to show.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands,tool/lookup-library-docs --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands,tool/lookup-library-docs,check/check-code-quality --repeat 3 --grade
```

!!! success "Key points"

    - A shadowed definition or an undefined name does not fail while the model writes, only at the grade.
    - `check/check-code-quality` runs `ruff --select F,E9` at the finish and hands back each error, at most twice.
    - Real errors only, never style, and silence when `ruff` cannot run.
    - Not measured as a lesson yet: the badge is `conjecture`.
