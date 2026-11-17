# LC.11B PR #1 recovery implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover the small, useful parts of PR #1 into focused changes based on current `main`, then comment the digest on PR #1 and leave it open without merging its stale documentation or conflicting branch.

**Architecture:** Treat PR #1 as a source of patches, not a branch to merge. Land harness fixes first, decide the guard and prompt changes separately, extract Flow/examine into its own design, and keep the current Getting Started docs.

**Tech Stack:** python harness, Pi TypeScript extensions, pytest, Node tests.

**Spec:** None. This is a recovery plan; Flow/examine needs a separate spec.

## Global Constraints

- Do not merge PR #1 wholesale; it conflicts with `main`.
- Do not copy its Getting Started, install scripts, glossary or baseline lesson changes.
- Every behavior change gets a test; every user-facing change gets a changelog entry.
- The Baseline Worker is the control. A guard or prompt change means a re-baseline before further comparisons.
- Flow/examine is a new architecture, not a remedy lesson.

## Review Focus

- The duplicate `grade()` must stay fixed; the later definition currently wins.
- A `.venv` file must not fail static grading.
- `--suite all` must be easy, medium, hard.
- PR #1’s baseline lesson change must never remove the `main` TypeScript sample.

---

### Task 1: Harness fixes

**Files:**
- Modify: `learn/code/harness.py`
- Test: `learn/code/tests/test_harness.py`

**Interfaces:**
- Produces: one `grade()` using Ruff `--select F,E9 --extend-exclude tests --extend-exclude grader_tests`.
- Produces: `run_suites` orders `easy`, `medium`, `hard`, then others.

- [ ] **Step 1: Write the failing tests**

Add a test that a `.venv/bad.py` with an undefined name does not fail `grade()`. Add a test for the suite ordering helper or `run_suites(["all"])` over a temporary `easy`/`medium`/`hard` directory.

- [ ] **Step 2: Run them and see them fail**

Run `uvx pytest learn/code/tests/test_harness.py -q`; expect the new tests to fail.

- [ ] **Step 3: Apply the three fixes**

Remove the shadowed second `grade()`. Change Ruff to `--extend-exclude`. Sort suites by `{"easy": 0, "medium": 1, "hard": 2}`.

- [ ] **Step 4: Run the harness tests**

Run `uvx pytest learn/code/tests -q --ignore=learn/code/tests/fixtures`.

- [ ] **Step 5: Commit**

`fix(harness): keep one F,E9 gate and order suites easiest-first`

### Task 2: Decide `confineToWorkspace`

**Files:**
- Compare: `extensions/mellum-guards.ts` at `pr-1`
- Test: `tests/mellum-guards.test.mjs`
- Record: `docs/superpowers/research/2026-10-24-workspace-confinement-screen.md`

- [x] **Step 1: Apply the guard alone on a branch, with its tests.** (`176922f`, branch `lc11b-confinement`)
- [ ] **Step 2: Run a small screen on one easy and one hard session.**
- [ ] **Step 3: If kept, re-baseline the Baseline Worker and update the worker page.**
- [ ] **Step 4: If rejected, record why and close the guard part.**

### Task 3: Decide prompt v6–v11

**Files:**
- Compare: `prompts/mellum-worker.md` at `pr-1`
- Record: `docs/superpowers/research/2026-10-24-prompt-v8-v11-triage.md`

- [x] **Step 1: Diff v5 against v11 and list every behavioral change.** v6–v11 mapped.
- [x] **Step 2: Check the existing ladder evidence for each change.** v7–v11 are ladder evidence; v6 is a recorded null; the foreground-server guard is extracted dormant in `420ba1d`, branch `lc11b-server-guard`.
- [x] **Step 3: Keep v11 only if its evidence survives; do not copy its AgentClinic-specific examples into a generic prompt.** Kept as ladder catalogue and lessons, not as the Baseline Worker.
- [ ] **Step 4: If kept, re-baseline the Baseline Worker.** Not triggered: Baseline Worker stays on v5.

### Task 4: Extract Flow/examine

Deferred to INT.2 on 2026-10-24; no Flow files were extracted here.

**Files:**
- Create from `pr-1`: `extensions/mellum-flow.ts`, `learn/code/flow_run.py`, `learn/code/tests/test_flow_run.py`, `tests/mellum-flow.test.mjs`
- Create: a new spec/plan for Flow after exploring it.

- [ ] **Step 1: Diff the flow files against `main` and list dependencies (`mellum-contract`, `mellum-knowledge`, `mellum-loop`, `mellum-plan`, `mellum-surgical`, `mellum-quality`, `mellum-verify`).**
- [ ] **Step 2: Decide which dependencies are required and which are experiments.**
- [ ] **Step 3: Rebase only the minimal flow/examine patch onto `main`.**
- [ ] **Step 4: Run one hard flow with visible and hidden results.**
- [ ] **Step 5: Write the Flow spec/plan before any package or Getting Started change.**

### Task 5: Comment on PR #1

**Files:**
- Update: `ROADMAP.md`, `CHANGELOG.md`, PR comment.

- [x] **Step 1: List the replacement commits/PRs for each accepted part.**
- [x] **Step 2: Comment on PR #1 with the split and archive links.**
- [x] **Step 3: Leave PR #1 open; do not close or merge it.**
- [x] **Step 4: Update LC.11B with the result and move the next work to LC.12.**

## Result

Closed 2026-10-24. The harness fixes are `2d8a86e`; the source map,
prompt triage, Flow triage and Intermediate candidates landed in `695adbf`.
The confinement and server guards are dormant on branches `176922f` and
`420ba1d`; no guard is enabled and the Baseline Worker is unchanged. The
[PR #1 comment](https://github.com/pauleveritt/mellum-worker/pull/1#issuecomment-6389192337)
was posted and the PR stays open. Flow/examine moved to INT.2. `npm test`
343/343; docs caps 4/4.
