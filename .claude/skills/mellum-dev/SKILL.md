---
name: mellum-dev
description: Use when developing in the mellum-worker repository — writing or editing specs, plans, research, the prompt, templates, extensions, the skill, the ladder, docs, or tests, and when committing, closing a phase, or cutting a release. Enforces the project's Superpowers SDD workflow, its document caps, test-first discipline, measured-settings rule, changelog discipline, and the worker-exit lead. Reflects AGENTS.md and docs/sdd.md, which are authoritative; this skill is the procedure, not new policy.
---

# mellum-dev — how we work in this repo

> 🍓 **Skill-active marker.** While this skill is guiding work in the
> mellum-worker repo, begin every reply with 🍓 — interim updates included.
> Drop it only when the conversation clearly leaves repo development.

`AGENTS.md` and [`docs/sdd.md`](../../../docs/sdd.md) are the source of truth.
This skill operationalizes them; where it and those files disagree, they win.
Read `AGENTS.md` first. Nothing here changes policy.

## 1. Spec-driven development (the cycle)

brainstorm → spec → plan → execute → review/close. Before writing any spec,
plan, or roadmap edit, read `docs/sdd.md`. Placement:
- Specs: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` — only when
  **product behavior** changes.
- Plans: `docs/superpowers/plans/YYYY-MM-DD-<topic>.md` — only when the work is
  large enough to need one. Front matter: `phase`, `cycle`, `lifecycle`.
- Research: `docs/superpowers/research/YYYY-MM-DD-<topic>.md` — opens with a
  **What is measured / What is conjecture** header, ends with **What would
  falsify this / Risks**.

**Evals: screens first, preregistered runs to decide.** While exploring, run
the fewest targeted runs that move the question and write a short research
note. Before a run that decides a default or a comparative claim, fix the
arms, n, scoring and rule in a preregistration. A screen is a **lead**, never
a rate. Do not re-open settled, measured decisions without a ladder run in
`ladder/`, recorded in `docs/ladder/`.

## 2. Test-first, both suites

- Every new test is **shown to fail first**, before the code that passes it.
- Node package suite (from the root): `npm test`.
- Python ladder suite (from `ladder/`): `uv run python -m pytest`
  (`-m "not slow"` for the fast subset). Never commit `trace.jsonl`,
  `stdout.txt` or `diff.patch`; raw ladder evidence goes in a
  `research-YYYY-MM-DD` release.
- CI (`.github/workflows/ci.yml`) runs the node suite and the ladder suite on
  every PR; it mirrors this local gate, it does not replace running it.

## 3. Measured settings are frozen without evidence

Do not change the prompt, templates, filter, tools, sampling or guards without
a ladder run in `ladder/` recorded in `docs/ladder/`. `prompts/mellum-worker.md`
is the **only** prompt source; run `node build.mjs` after editing it (a test
fails on template drift). A setting the shipped product does not use is a
harness finding, not a claim about the worker.

## 4. Document caps are not advisory

`ROADMAP.md` 400 lines; a Ships/Excludes cell 900 chars; a Status cell 1,000;
a backlog entry 1,200; a plan 400 lines and 25% fenced; a spec 400 lines.
`tests/docs-caps.test.mjs` enforces them. **Over cap means a research or verdict
doc is owed** — move the narrative to `docs/superpowers/research/` and link it —
**not that the wording gets trimmed.** `## Now` is a pointer, never a narrative.
Every backlog entry states a reopen condition; remove resolved/retired/superseded
entries. Preserve reversed decisions with dated corrections; never edit archived
plans.

## 5. Keep the changelog current

Update `CHANGELOG.md`'s `## [Unreleased]` in the **same commit** as any change to
what a user installs, runs, configures or reads (extensions, prompt, templates,
skill, README, recipe, the ladder's commands or records), under the existing
Added / Changed / Fixed / Removed headings. **Internal-only commits — SDD
records, backlog, roadmap, tests, CI, this skill — need no entry.** Entries say
what changed for the user and why, not the commit subject. Never add a `build`,
`prepare`, `prepack`, or `install` npm script (it breaks the pacote install).

## 6. Driving the worker (a lead under test)

Don't trust the worker's self-exit: a run can go green on an incomplete,
self-authored test. The direction being measured is an acceptance test that is
**external, complete and unweakenable**, with the exit verified by re-running
it and re-dispatching the failure. This is M.11 + the freeze-the-oracle guard,
**unmeasured until M.11's rung-9 screen** — a lead, not a rule. See the
[exit-gate note](../../../docs/superpowers/research/2026-10-18-harness-exit-gate.md).

**Making "complete" real.** "Complete" is the load-bearing word, so verify it
before trusting a mediated acceptance test. The test must be a **superset of the
rung's hidden oracle** (`ladder/fixtures/agentclinic-hidden/_hidden_pN.py`): it
checks everything the oracle checks, plus the spec requirements the oracle leaves
thin. Author it from the spec, never from the worker's output. Dry-run it (plain
pytest, no model): it **and** the oracle pass the complete
`ladder/fixtures/agentclinic-done` implementation (green), and the test **fails**
a build with the known miss — e.g. Phase 4's id assigned in the route only, not
on `Complaint` (red). A test that cannot go red on the failure mode is not
complete, whatever it covers.

## 7. Finishing a phase

Update the phase Status cell and `## Now` in `ROADMAP.md`; write the plan's
`## Result`, set `lifecycle: closed|superseded`, move it to
`plans/archive/`; remove any backlog entry it resolved. Confirm every claim
against its linked evidence, pass `node --test tests/docs-caps.test.mjs` and
`npm test`, and reconcile `[Unreleased]`. A phase may close before a release
tag. A release is a tag where `package.json`, the tag, both README install
lines and a `CHANGELOG.md` section agree.

## 8. Coding principles (our developer coding standards)

Our general developer discipline, kept to what transfers to this repo (nothing
framework-specific — no routes, ORM or journeys):

- **Real tests, no mocks.** A change to our own code gets named positive *and*
  negative tests, run against real dependencies — real fixtures, servers,
  SQLite — not mocks. The ladder and the node suite already work this way.
- **Use the real harness; scaffold, don't hand-roll.** Exercise the shipped
  path — `run_ladder`, Pi, the real guards — not a throwaway stand-in. A result
  from a scratch driver is a lead at best; conclusions come from the real
  harness. (This is why `--acceptance-test` lives in the ladder, not a script.)
- **Built-ins and zero dependencies first.** The package ships dependency-free
  and the ladder has none; reach for the standard library and existing code
  before a dependency, and never for one an install script would need (pacote
  breaks on `build`/`prepare`/`prepack`/`install` scripts).
- **Security by default.** Secrets live in `.env`, never in code, logs, URLs or
  run records; fail safe (no secret or stack trace to a user-facing surface);
  parameterise any SQL.
- **Earn the claim.** State a result only when real evidence backs it — a green
  test, a recorded ladder run — and label a screen as the lead it is. This is
  the measured-settings and screens-first rules, said as a habit.

## 9. Run it where the user can see it

Never bury a test run or a ladder run in a hidden background call. The user
watches it happen:

- **Tests** go in the Terminal panel (`run_in_terminal`), and the pane is
  **opened on that tab** (`show_pane` terminal, `tab_id`). Prefer verbose
  (`uv run python -m pytest -v`, per-test names; `npm test`).
- **A ladder run** (`run_ladder`) prints only its final row, so it is not
  watchable on its own. **Default, every run, no exceptions:** start
  `python scripts/watch_ladder.py` in a Terminal tab and `show_pane` it
  *before* launching the run. It follows the newest per-rung `trace.jsonl` and
  prints each worker turn (thinking + tool calls) live, switching to the next
  rung's trace automatically — so **every rung**, not just the first, streams in
  front of the user. A ladder run without this follower on screen is a bug.
- A tab the user cannot see is the same as no visibility — always
  `show_pane` the live tab. If a run is long, say where to look and keep it on
  screen.

## 10. One PR per win or learning

Every verified win and every real learning lands as its own small, focused PR
**to upstream** (`pauleveritt/mellum-worker`), opened from our fork — never
batched into a grab-bag. One change, one reason, one review.

- **A win** is a *measured* improvement: a ladder pass-rate gain (before → after
  rows), or a confirmed fix. A lead or a screen is **not** a win yet — see §3;
  only open the PR once a preregistered run backs the claim.
- **A learning** is a result worth keeping even when nothing ships — most often
  a plausible "optimization" the ladder caught as a *regression*, or a
  hypothesis the evidence disproved. Negative results are first-class; they stop
  us re-running the same dead end.

What each PR carries:

- **Win PR:** the one focused change, its `CHANGELOG.md` `[Unreleased]` entry
  (§5), and the ladder evidence inline in the body (the before/after rows, n,
  deadline, model). Nothing unrelated rides along.
- **Learning PR:** a dated research note under
  `docs/superpowers/research/YYYY-MM-DD-<topic>.md` stating the hypothesis, what
  was run, the result that settled it, and the decision — plus the one-line
  `BACKLOG.md`/`ROADMAP.md` pointer if it moves a lead. The code change is just
  the revert, or none.

How:

- Branch off **`upstream/main`** (fetch it first), not our fork's `main`, so the
  PR is a clean, separable diff and never stacks another open PR's commits on
  top; stage **explicit paths** only (never `git add -A`); keep it small enough
  to read in one sitting. Push the branch to our fork (`origin`) and open the PR
  against `upstream`.
- Never commit `trace.jsonl`, `stdout.txt` or `diff.patch`; raw evidence goes in
  a `research-YYYY-MM-DD` release, linked from the note (per `AGENTS.md`).
- Title is a concise `{feat,fix,docs}` subject; the body **leads with a short
  table** — *what changed · why · evidence* — then detail. End with the
  AI-generated attribution line the prompt specifies.
- Keep the framework name out of every PR title, body and commit (standing
  constraint).

## 11. Record every run that backs a claim

Scratchpad runs are ephemeral. A measured result that backs a win or a learning
is recorded **in the repo** before (or with) its PR — never left in `/tmp`:

- **The record** → `docs/ladder/<YYYY-MM-DD-topic>/`: the `table.md` and, per
  run, its `rung…-r{k}/run.json` (plus `final.md`/`brief.md`). Strip the raw
  `trace.jsonl`, `stdout.txt`, and `diff.patch` — those never go in the tree.
- **The note** → `docs/superpowers/research/YYYY-MM-DD-<topic>.md`: arms, n, the
  rule, the result, and the decision (§3). It links the record and the release.
- **Raw evidence** → a `research-YYYY-MM-DD` tag/release, linked from the note.
- **Provenance** → when records move in from elsewhere, say from where and at
  what commit (see `docs/ladder/PROVENANCE.md`).

The win/loss PR (§10) carries the record and the note. A claim with no committed
record behind it is a lead, not a result.
