---
phase: LC
feature_cycle: LC.24
cycle: 1
lifecycle: closed
---

# Lesson 1 as the Exemplar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Lesson 1 so it names a pathology and a mechanism, open it with a two-sentence paragraph, and give it `reference-run` from one preregistered easy+medium run at n=3 per arm.

**Architecture:** Documentation and one measurement. The badge is re-pointed from `ladder/` to `learn/code/harness.py` first, because the page's claim depends on it; the template carries the new paragraph rule; the page is rewritten; a preregistration precedes a 12-session run; the record and the badge change land together.

**Tech Stack:** Markdown lessons under `learn/`, Node's test runner, `uv run python learn/code/harness.py`, llama.cpp on `127.0.0.1:8002`.

**Spec:** `docs/superpowers/specs/2026-10-25-lc24-lesson1-exemplar-design.md`

## Global Constraints

- Terse paragraph: between the H1 and `## Problem`, no heading, exactly two sentences, 45 words or fewer, no badge, no link, no code span.
- `reference-run` requires: a preregistration written before the run naming lesson, arms, n, reading and decision rule; the record in `docs/superpowers/research/`; raw evidence in a `research-*` release; machine and deadline in the record.
- Run settings: suites `easy` and `medium`, arms `bare` and `worker`, `--repeat 3`, `--grade`, `--deadline 1800`.
- Lesson pages may not link `evals/` (seven tests assert it).
- Do not edit `ladder/` or `evals/`; do not delete them.
- Never commit `trace.jsonl`, `stdout.txt` or `diff.patch`.
- Caps: plan 400 lines and 25% fenced, roadmap Ships/Excludes 900 chars, Status 1,000, spec 400.

Content blocks below are shown as quotes: copy the text without the `>` markers.

---

### Task 1: The cycle row and the Now pointer

**Files:**
- Modify: `ROADMAP.md` (the `## Now` block; a new row after `LC.23`)

**Interfaces:**
- Consumes: nothing.
- Produces: the row id `LC.24` that later commits and the plan header name.

- [ ] **Step 1: Add the row** after `LC.23`, matching the table's column widths:

> | **LC.24**  | Lesson 1 as the exemplar: the page names a pathology and the three decisions the worker takes, opens with a two-sentence paragraph, and carries `reference-run` from one preregistered easy+medium run at n=3 per arm; the template gains that paragraph's rule; `reference-run` re-points from `evals/` to the suites, and the pages that call `ladder/` the measured instrument follow. | Migrating the other eight lesson pages; editing or deleting `ladder/` or `evals/`; prompt, guard, tool or facts changes; a rate, or a claim that transfers off this machine; re-planning LC.19. | in progress 2026-10-25 — [spec](docs/superpowers/specs/2026-10-25-lc24-lesson1-exemplar-design.md), [plan](docs/superpowers/plans/2026-10-25-lc24-lesson1-exemplar.md). |

- [ ] **Step 2: Move the pointer.** In `## Now`, `**Active:**` becomes `**Active:** LC.24, Lesson 1 as the exemplar — the page rewritten, the two-sentence convention, and `reference-run` earned on the suites.`; `**Next:**` becomes `**Next:** LC.18, then LC.19, whose instrument needs a suite before it can start, then LC.7A.`

- [ ] **Step 3: Note LC.19's loss.** Append to LC.19's Status cell: `**2026-10-25:** its instrument was ladder rungs 6–9; LC.24 retires the ladder from the lessons, so LC.19 owes a suite-shaped instrument before it can start.`

- [ ] **Step 4: Verify caps and commit.**

Run: `node --test tests/docs-caps.test.mjs` — expect 4/4.

```bash
git add ROADMAP.md && git commit -m "docs(lc24): take lesson 1 as the active cycle"
```

### Task 2: Re-point `reference-run` at the suites

**Files:**
- Modify: `learn/about/evidence.md:9-10`, `learn/glossary.md:60-63`, `learn/getting-started/harness.md:13-16,107-109`, `learn/project/index.md:14-15`, `learn/project/toolchain.md:71-72`, `CHANGELOG.md`
- Test: `tests/learn-site.test.mjs`

**Interfaces:**
- Consumes: nothing.
- Produces: the wording Task 6 assumes when it badges the page.

- [ ] **Step 1: Write the failing tests.** Append to `tests/learn-site.test.mjs`:

```js
test("reference-run is earned on the suites, not the ladder", () => {
  const evidence = page("about/evidence.md");
  const row = evidence.split("\n").find((l) => l.startsWith("| `reference-run`"));
  assert.ok(row, "no reference-run row");
  assert.match(row, /preregistration/);
  assert.doesNotMatch(row, /docs\/ladder\//);
  assert.match(evidence.split("\n").find((l) => l.startsWith("| `cited`")), /docs\/ladder\//);
  const entry = page("glossary.md").split("### reference-run")[1].split("###")[0];
  assert.match(entry, /preregistered run on llama\.cpp/);
  assert.doesNotMatch(entry, /ladder run/);
});

test("the harness is the measured instrument", () => {
  const harness = page("getting-started/harness.md");
  assert.doesNotMatch(harness, /`ladder\/` is the measured instrument/);
  assert.doesNotMatch(harness, /do not replace `docs\/ladder\/`/);
  assert.match(harness, /`learn\/code\/harness\.py` is the measured instrument/);
  assert.doesNotMatch(page("project/index.md"), /\*\*The ladder\*\*/);
  assert.match(page("project/toolchain.md"), /Measured work lands in `docs\/superpowers\/research\/`/);
});
```

- [ ] **Step 2: Run and see both fail.** `node --test tests/learn-site.test.mjs` — expect 2 failures.

- [ ] **Step 3: Rewrite the two badge rows** in `evidence.md` (the `reference-run` row loses `evals/`, keeps `preregistration`; the `cited` row keeps `evals/`, marked `(pre-2026-10-25)`, and offers `or a research note on main`):

> | `reference-run` | A preregistered run on llama.cpp, made for this lesson, on the suites the course teaches | A preregistration written before the run naming the lesson, the arms, n, the reading and the decision rule; the record in `docs/superpowers/research/`; raw evidence in a `research-*` release; machine and deadline in the record |
> | `cited` | An existing record made before 2026-10-25 | A record in `evals/` (pre-2026-10-25) or a research note on `main` |

- [ ] **Step 4: Rewrite the glossary entry** at `### reference-run`:

> A preregistered run on llama.cpp, made for a lesson, on the suites the course
> teaches. Earned with a preregistration written before the run, the record in
> `docs/superpowers/research/`, and raw evidence in a `research-*` release.

- [ ] **Step 5: Flip the four instrument sentences.**

`harness.md:14-16` → ``It is a teaching tool; `learn/code/harness.py` is the measured instrument, and findings lessons cite the suites.``
`harness.md:107-109` → ``They are not preregistered and they run on one machine; a lesson's `reference-run` is the preregistered version of the same run.``
`project/index.md:14-15` → ``- **The harness**: `learn/code/harness.py` and the easy/medium/hard suites, the instrument the lessons measure with. `ladder/` reruns rungs 1–9 internally and is no longer the lessons' instrument.``
`toolchain.md:71` → ``Measured work lands in `docs/superpowers/research/` with its preregistration; raw evidence``

- [ ] **Step 6: Changelog.** Under `[Unreleased]` → `### Changed`:

> - `reference-run` is earned on the suites now, not on `ladder/`: the badge
>   names a preregistration, a record in `docs/superpowers/research/` and a
>   `research-*` release. `ladder/` and `evals/` stay as the internal
>   instrument and the A0–A21 archive.

- [ ] **Step 7: Run and see both pass, then commit.**

Run: `node --test tests/learn-site.test.mjs` — expect 0 failures.

```bash
git add learn tests CHANGELOG.md && git commit -m "docs(lc24): earn reference-run on the suites"
```

### Task 3: The two-sentence rule in the template

**Files:**
- Modify: `learn/lesson-template.md`
- Test: `tests/learn-site.test.mjs`

**Interfaces:**
- Consumes: nothing.
- Produces: the rule and placeholder Task 4 copies onto the page.

- [ ] **Step 1: Write the failing test.** Append to `tests/learn-site.test.mjs`:

```js
test("the lesson template opens with the two-sentence paragraph", () => {
  const t = page("lesson-template.md");
  const opening = t.split(/^# .+$/m)[1].split(/^## /m)[0].trim();
  assert.ok(opening.length > 0, "template has no opening paragraph");
  assert.equal(opening.split(/(?<=\.)\s+/).filter(Boolean).length, 2);
  assert.ok(opening.split(/\s+/).length <= 45, "opening is over 45 words");
  assert.match(t, /two sentences/);
});
```

- [ ] **Step 2: Run and see it fail** on `template has no opening paragraph`.

- [ ] **Step 3: Add the placeholder and the rule** after the file's H1, before `## Problem`:

> The problem in one sentence. The solution in one sentence.
>
> *(Two sentences, 45 words or fewer, no heading, no badge and no link: the
> paragraph a reader sees before the six steps.)*

- [ ] **Step 4: Run and see it pass, then commit.**

Run: `node --test tests/learn-site.test.mjs` — expect 0 failures.

```bash
git add learn/lesson-template.md tests/learn-site.test.mjs && git commit -m "docs(lc24): put the two-sentence opening in the template"
```

### Task 4: Rewrite Lesson 1

**Files:**
- Modify: `learn/lessons/primary-agent.md` (opening, `## Problem`, `## Solution`, `## Interpretation`)
- Test: `tests/lesson-primary-agent.test.mjs` (new)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: the template rule from Task 3.
- Produces: a page whose steps 3 and 5 Task 6 re-badges, and the `section(h)` helper Task 6 reuses.

- [ ] **Step 1: Write the failing test.** Create `tests/lesson-primary-agent.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const l = readFileSync(resolve(import.meta.dirname, "..", "learn/lessons/primary-agent.md"), "utf8");
const section = (h) => l.split(`## ${h}`)[1].split(/\n## /)[0];

test("lesson 1 opens with the two-sentence paragraph", () => {
  const opening = l.split(/^# .+$/m)[1].split(/^## /m)[0].trim();
  assert.equal(opening.split(/(?<=\.)\s+/).filter(Boolean).length, 2);
  assert.ok(opening.split(/\s+/).length <= 45, "opening is over 45 words");
  assert.doesNotMatch(opening, /`|\]\(|\*\*Badge/);
});

test("lesson 1 states the pathology, not just the outcome", () => {
  assert.match(section("Problem"), /confident final over work it never checked/);
  assert.doesNotMatch(l, /Give Mellum the whole job/);
});

test("lesson 1 names the three decisions the worker takes", () => {
  const s = section("Solution");
  assert.doesNotMatch(s, /Do not make the model the main agent/);
  for (const t of ["setActiveTools", "before_provider_request", "agent_before_settle"])
    assert.ok(s.includes(t), `solution lacks ${t}`);
});

test("lesson 1 does not claim every medium session was killed", () => {
  assert.doesNotMatch(l, /every medium session, both arms, was killed/);
  assert.match(l, /359 s/);
  assert.match(l, /204 s/);
});
```

- [ ] **Step 2: Run and see four failures.** `node --test tests/lesson-primary-agent.test.mjs`

- [ ] **Step 3: Add the opening paragraph** after the H1:

> The primary agent lets one small model plan, choose and decide it is finished,
> so a confident final over unchecked code is the result. The worker takes those
> three decisions out of the model's text and leaves the plan and the verdict
> with you.

- [ ] **Step 4: Replace `## Problem`'s body** (the badge line stays `screen`):

> Ask Mellum to own the plan, pick the tools and decide it is finished, and the
> failure is not a wrong answer: it is a confident final over work it never
> checked. Nothing outside the model knows what "finished" meant, so a missed
> phase, a narrowed test or a hang arrives as your result, and the turns, the
> context and the wall clock arrive as your bill.
>
> That is the pathology. This page tests whether moving the plan and the stop
> condition out of the model's hands answers it, and the evidence is thinner
> than the claim the page used to make: on easy an unbounded Pi finished one
> session in three, and the old 8/15 is retired. What survives is the shape of
> the bound and the baseline's medium contrast, 2/3 against 0/3.

- [ ] **Step 5: Replace `## Solution`'s body** (no longer true that the badge is unused):

> The model is not the thing you change. Pi is the main agent in both arms and
> Mellum is the model inside it; what changes is which decisions the model's own
> text is allowed to make. The worker takes three of them
> (`extensions/mellum-worker.ts`):
>
> - **Which tools exist:** `pi.setActiveTools(WORKER_TOOLS)` narrows the set to
>   seven file tools — `read`, `grep`, `find`, `ls`, `bash`, `edit`, `write`
>   (line 411).
> - **What the instructions are:** `before_provider_request` replaces the system
>   message with prompt v5, whose last line defines done as "the test command
>   exits 0" (line 577).
> - **Whether the turn is finished:** `agent_before_settle` can refuse to settle
>   an empty turn, up to three times, and the loop breaker blocks the next
>   identical tool call after five (line 614).
>
> The plan stays with the operator — one task per `/mellum` — and in a measured
> run the verdict is a separate act: the hidden tests are copied in and scored
> after the model has stopped talking.
>
> The guard is the thinnest of the three: on easy it never fired, zero nudges in
> ten sessions (LC.13A), so what carried those runs was the test command and the
> operator's scoring.

- [ ] **Step 6: Correct the Interpretation's last paragraph:**

> What would upgrade this: n larger than three, and a medium run on a machine
> and deadline that let the suite finish. Medium fits 600 s on the M5 Max where
> the baseline ran — Baseline Pi 0/3 at 359 s, Baseline Worker 2/3 at 204 s —
> and does not on the M1 Pro, roughly 1.7–3× slower, where medium now runs with
> `--deadline 1800`. Until then the honest sentence is "on easy, an unbounded Pi
> sometimes finishes; on medium, the baseline's primary agent did not in nine
> sessions".

- [ ] **Step 7: Changelog.** Under `[Unreleased]` → `### Changed`:

> - Lesson 1, "The primary agent is the wrong worker", now opens with a
>   two-sentence summary, names the pathology before the measurement, says which
>   three decisions leave the model's hands instead of advising against a role,
>   and stops claiming every medium session was killed at 600 s.

- [ ] **Step 8: Run the suite and commit.**

Run: `node --test tests/learn-site.test.mjs tests/lesson-primary-agent.test.mjs` then `npm test` — expect 0 failures.

```bash
git add learn/lessons/primary-agent.md tests/lesson-primary-agent.test.mjs CHANGELOG.md
git commit -m "docs(lc24): rewrite lesson 1 around the pathology and the mechanism"
```

### Task 5: Preregister the run

**Files:**
- Create: `docs/superpowers/research/2026-10-25-lesson1-preregistration.md`

**Interfaces:**
- Consumes: the arms and settings in Global Constraints.
- Produces: the file Task 6's record cites, and the decision rule it must apply.

- [ ] **Step 1: Write the file** with these sections, all values as given:

- **What is measured** — the `bare` vs `worker` contrast on easy and medium, n=3 per arm, no rate.
- **Arms** — one table row each: `bare` = Pi with no extension, the primary agent; `worker` = prompt v5, seven file tools, the empty-final nudge, the loop breaker and project facts.
- **Settings** — `llama-server` 0.7.0, Mellum 2.1 `Q4_K_M`, `-c 50000` (`n_ctx` 50,176), `127.0.0.1:8002`; Apple M1 Pro, 8 cores, 32 GiB; `--repeat 3 --grade --deadline 1800`; calibration: LC.17 finished medium at 894 s and 961 s at this deadline on this machine, so 1800 s is 1.9× the observed wall.
- **Cost** — 12 sessions, about two hours.
- **Reading** — passes per suite, failed checks, tool errors, peak input, wall, and the `deadline` marker.
- **Decision rule** — per suite: if `worker` passes strictly more sessions than `bare`, the page states a count of sessions at n=3; otherwise it states a null. No arm, suite, n or reading changes after the run; a session the deadline ended is reported as censored, never as a failure.
- **Either outcome publishes** — a null returns those steps to `screen` and the page says so.
- **What would falsify this** — a `bare` request carrying `Project facts:`, or a `worker` arm passing zero sessions on both suites.

- [ ] **Step 2: Commit before running.**

```bash
git add docs/superpowers/research/2026-10-25-lesson1-preregistration.md
git commit -m "docs(lc24): preregister lesson 1's easy and medium run"
```

### Task 6: Run it, record it, badge it

**Files:**
- Create: `docs/superpowers/research/2026-10-25-lesson1-run.md`
- Modify: `learn/lessons/primary-agent.md` (steps 3 and 5 badges, evidence tables, Interpretation), `tests/lesson-primary-agent.test.mjs`, `CHANGELOG.md`

**Interfaces:**
- Consumes: the preregistration and its decision rule, and `section(h)` from Task 4.
- Produces: the record the badge points at.

- [ ] **Step 1: Start the backend.** `uv run scripts/backend.py start`, then `uv run scripts/backend.py status` — expect `up`.

- [ ] **Step 2: Run both suites, both arms.**

```bash
uv run python learn/code/harness.py run --suite easy --arm bare --repeat 3 --grade --deadline 1800
uv run python learn/code/harness.py run --suite easy --arm worker --repeat 3 --grade --deadline 1800
uv run python learn/code/harness.py run --suite medium --arm bare --repeat 3 --grade --deadline 1800
uv run python learn/code/harness.py run --suite medium --arm worker --repeat 3 --grade --deadline 1800
```

- [ ] **Step 3: Write the record** at the path above: the four tables (suite, arm, passes, failed checks, tool errors, peak input, wall, ended-on), the machine and deadline, the reading the rule produced, and anything the preregistration did not anticipate. Copy no `trace.jsonl` or workspace into Git.

- [ ] **Step 4: Write the failing badge test**, appending to `tests/lesson-primary-agent.test.mjs`:

```js
test("lesson 1's evidence steps carry reference-run", () => {
  for (const h of ["Evidence of the problem", "Validation"])
    assert.match(section(h), /^\n+\*\*Badge:\*\* `reference-run`/);
});
```

Run `node --test tests/lesson-primary-agent.test.mjs` — expect one failure.

- [ ] **Step 5: Apply the decision rule and the badge.** Under `## Evidence of the problem` and `## Validation`, replace the per-session tables with the new run's, keep the baseline rows for contrast, state a count of sessions or a null exactly as the rule requires, and change both step badges from `` `screen` `` to `` `reference-run` ``.

- [ ] **Step 6: Update the Interpretation.** Its weakest-badge sentence names the new badge and the run's limits, and a dated line records the change: `Changed 2026-10-25: steps 3 and 5 moved from `screen` to `reference-run` on [the record](2026-10-25-lesson1-run.md).`

- [ ] **Step 7: Publish raw evidence** as a `research-2026-10-25` release holding the run directories without `workspace/` or `profile/`, then add its URL to the record and amend the Task 4 changelog bullet to name the run.

- [ ] **Step 8: Run everything and commit.**

Run: `npm test` and `node --test tests/docs-caps.test.mjs` — expect 0 failures and 4/4.

```bash
git add learn tests docs CHANGELOG.md
git commit -m "docs(lc24): record lesson 1's reference run and badge it"
```

### Task 7: Close the cycle

**Files:**
- Modify: `ROADMAP.md` (LC.24 Status, `## Now`), this plan
- Move: this plan to `docs/superpowers/plans/archive/`

**Interfaces:**
- Consumes: every earlier task's outcome.
- Produces: a closed cycle and an archived plan.

- [ ] **Step 1: Write `## Result`** in this plan: the date, what shipped, the run's numbers, the badge outcome, and what is still owed (the other eight pages, LC.19's instrument).

- [ ] **Step 2: Set LC.24's Status cell** to the form `complete YYYY-MM-DD — [spec](docs/superpowers/specs/2026-10-25-lc24-lesson1-exemplar-design.md), [plan](docs/superpowers/plans/archive/2026-10-25-lc24-lesson1-exemplar.md), [record](docs/superpowers/research/2026-10-25-lesson1-run.md), [lesson](learn/lessons/primary-agent.md).` followed by the run's headline numbers, the badge outcome and the `npm test` total — all copied from the record written in Task 6, and within 1,000 chars.

- [ ] **Step 3: Move `## Now` on** — `**Active:**` names the next cycle; `**Shipped:**` is unchanged.

- [ ] **Step 4: Archive.** `git mv docs/superpowers/plans/2026-10-25-lc24-lesson1-exemplar.md docs/superpowers/plans/archive/` and set `lifecycle: closed`.

- [ ] **Step 5: Reconcile the changelog** against `git log e6c8fd5..HEAD --oneline`, then run `npm test` and `node --test tests/docs-caps.test.mjs` once more.

```bash
git add -A && git commit -m "docs(lc24): close the cycle"
```

## Result

2026-10-25. Shipped: Lesson 1 rewritten (pathology-first Problem, the three
decisions named with file:line, terse two-sentence opening), the rule in
`learn/lesson-template.md`, `reference-run` re-pointed from `evals/` to
the suites with the four instrument sentences following, one preregistered run
of twelve sessions, its record, and `research-2026-10-25`.

The run came back **null on both suites** — easy 1/3 against 1/3, medium 0/3
against 0/3 — and the baseline's medium 2/3 against 0/3 did not reproduce, so
steps 3 and 5 carry `reference-run` for a null and the page now argues from
the cost of failing: two of three `bare` easy sessions censored on a
foreground server and `main.py` written outside the layout twice, against none
for `worker`. `npm test` 366/366, `docs-caps` 4/4.

Owed and recorded elsewhere: the other eight lesson pages' terse paragraphs
(follow-up), LC.19's suite-shaped instrument (its row), and the `wall` metric
that understates censored sessions ([backlog](../BACKLOG.md#backlog)).
