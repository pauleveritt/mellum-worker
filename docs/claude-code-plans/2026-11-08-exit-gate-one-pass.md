# Plan — Exit-gate the one-pass worker to a reliable full medium pass

## Context

One agent building the whole section in a **single pass** (no architect, no step
docs, no delegation) beats the shipped architect-split plan loop ~5× on requests
at equal-or-better score — but medium is a **coin-flip**: a full 18/18 on only
2 of 4 converged reps, floor 15–16. It self-exits on its own weak suite and never
closes the deep **Phase-4** contract (the complaint id must be an auto-increment
default *on the dataclass* so two direct constructions get distinct ids — the
hidden oracle builds `models.Complaint("a","b")` directly; the agent assigns the
id in the add-route, which passes the happy path and fails direct construction).

A prose nudge does not fix this — a second screen with a stronger agnostic
preamble still landed 18/18 only half the converged reps. AGENTS.md is explicit:
for a fixed small model, **prefer a harness guarantee over a prose rule**. The
guarantee already exists in the repo — the worker just never loaded it on the
one-pass path, and there is no complete medium acceptance test to point it at.

**The paradigm (the user's framing):** one pass, then *a check with a small turn
afterwards* — re-run an external, complete, frozen acceptance test at settle, and
while it is red, hand the agent back only its failing test functions for a short
corrective turn, looping to green. Build the missing acceptance test, wire the
existing gate to the one-pass run, and measure whether it converts the coin-flip
into a reliable 18/18 at a cost still well under the architect loop.

## What already exists — reuse, do not rebuild

- `extensions/mellum-verify.ts` — an `agent_before_settle` gate: runs `VERIFY_TEST`
  (a named test) or `VERIFY_ALL` (whole suite), and while red returns
  `{continue:true}` with the **failing test functions** named, up to `VERIFY_MAX`
  (default 5). Self-contained (`-e` load), runs with `PYTHONPATH=cwd` so a test
  placed outside the workspace still `from app import app`. Works in any session,
  Mellum Mode included — so it engages on the one-shot child's settle.
- `extensions/mellum-acceptance.ts` — **Tier-1** agnostic structural gate (app
  boots + every spec-named route registered, param-normalized). Free, no
  authoring. Deliberately **shallow** — will not catch the deep Phase-4 invariant.
- `ladder/fixtures/acceptance/test_phase5–7.py` — the authoring convention for a
  **frozen, spec-derived, superset-of-the-oracle** acceptance test. No phase-1–4
  equivalent exists; that gap is the real work here.
- The one-pass path: `extensions/mellum-worker.ts` `CHILD_ENV` one-shot
  (`sendUserMessage` → `waitForIdle` → settle) fires `agent_before_settle`, so the
  gate loops within the same run.

## The one design decision

The deep gate needs a **complete medium acceptance test**. Author it **once, by
hand, from the spec** (a static Tier-2 test) — not a per-run examiner model (keeps
the one-pass cost; no extra model), and not the grader itself (that is coding to
the eval). Place it **outside the workspace** and point `VERIFY_TEST` at its
absolute path, so the agent never sees or can weaken it (no freeze-guard needed).

## Workstreams

### 1. Author the complete medium acceptance test (the committed artifact)

New `ladder/fixtures/acceptance/test_medium.py` (phases 1–4 in one file),
authored from `learn/code/suites/medium/prompts/01–04.md`, a **superset** of the
hidden oracle, in the `test_phase5.py` style (`import models`, `from app import
app`, `TestClient(app, follow_redirects=False)`). Asserts:
- **P1**: `GET /` 200 + tagline "Come in. Sit down. Tell us about your human.";
  base layout — doctype, `lang="en"`, navbar brand "AgentClinic", Home/Complaints links.
- **P2**: `GET /complaints` 200 + `Scope creep never ends.`; `Complaint` has
  `agent_name`/`text`/`timestamp`; seed `complaints` list; card shows name, a
  Y-M-D date, text.
- **P3**: form (POST `/complaints`, `agent_name` + `text`); `POST /complaints`
  (`follow_redirects=False`) → 303, `Location: /complaints`; new complaint appears.
- **P4 (the deep one)**: `Complaint("a","b")` constructs positionally; two direct
  constructions get **distinct** ids; `status` defaults `"open"`; `POST
  /{id}/resolve` → `resolved` + 303 to `/complaints`; `POST /{id}/reopen` → `open`
  + 303; badge "Open"/"Resolved"; Resolve/Reopen buttons; order and ids unchanged
  across resolve+reopen.

### 2. Prove the test is complete, not a ghost (skill §6) — before any model run

- **GREEN**: the new test **and** the hidden oracle both pass on
  `ladder/fixtures/agentclinic-done` under plain pytest (no model).
- **RED**: the new test **fails** a build with the Phase-4 id-in-route miss —
  shown on the existing 15/18 one-pass workspace (scratch `opmr2-r1`) and/or a
  no-phase-4 fixture. A test that cannot go red on that miss is not complete.

### 3. Wire the gate into the one-pass run (scratch rig)

A scratch script (shaped like `one-pass-medium-refine.sh`) that adds to the
one-pass child: `-e extensions/mellum-verify.ts`, `VERIFY_TEST=<abs path to
test_medium.py>`, `VERIFY_MAX=5`, `VERIFY_PYTEST="uv run --offline python -m
pytest"`. Revert the preamble to the **lean** pre-refine one — the gate, not the
prose, now closes the gap. (Optionally also `-e mellum-acceptance.ts` for the free
structural layer.)

### 4. Measure — the real check

One-pass medium **n=3** with the gate on, visible in a Terminal tab. Record:
full-pass rate (want 3/3 = 18/18), redispatch turns used, total requests (one pass
~70 + the corrective turns), wall — against the ungated coin-flip (18/18 on 2 of
4) and the architect loop (300+ req).

### 5. Record and decide

Update `docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md` (or a
new dated note) with the gated result. If it reliably reaches 18/18 at a cost ≪
the architect loop, that is the answer to the paradigm; note whether it should
become a ladder mode (one-pass + `--acceptance-test`, analogous to `--mode plan`)
for a preregistered `run_ladder` verdict.

## Out of scope (now)

- A ladder `--mode one-pass` / preregistered `run_ladder` verdict (follow-up once
  the scratch rig shows the gate works).
- A per-run examiner model (Tier-2 dynamic); easy-tier gating; the plan-loop path.

## Verification

- The §2 dry-runs (green-on-done, red-on-miss) gate the work before any model run.
- The §4 n=3 gated medium run, tally streamed in a Terminal tab.
- **No shipped/product-config change** in this step — scratch rig only; the single
  committed artifact is the `test_medium.py` fixture (plus the research note).
  `npm test` is unaffected (a fixture, not a code path). The measured-settings
  freeze does not apply (no prompt/template/sampling/guard/remedy change).
