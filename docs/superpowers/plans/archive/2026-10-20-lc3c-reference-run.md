---
phase: LC.3C
cycle: 1
lifecycle: closed
---

# LC.3C Reference run implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A preregistered, valid 15-run reference on llama.cpp, recorded in `evals/` with its pass counts, and citable by lessons as `reference-run`.

**Architecture:** The preregistration fixes the arms, n, reading and decision rule before any run. The ladder's backend flags (LC.3B) run the 15 rows; the record is a `evals/` directory with a README, `table.md` and each run's `run.json`, while raw traces stay out of git for a release.

**Tech Stack:** `ladder/` (`uv run python -m ladder.run_ladder`), llama.cpp on port 8002, Markdown records.

**Spec:** [Learning Center design](../specs/2026-10-20-learning-center-design.md) §6 (`reference-run`); [preregistration](../research/2026-10-20-llamacpp-reference-preregistration.md).

## Global Constraints

- The preregistration is written and committed before the run; it is not edited after the results are seen.
- 15 runs: rungs 1–5, three repeats, direct/baseline, greedy params, deadline 600, llama.cpp on 8002.
- Validity: every run's first `provider_request` carries the greedy block and `max_tokens` 4096; an invalid run is named and excluded, never silently.
- No promotion, no worker change, no oMLX comparison. Raw evidence never enters git.

## Review Focus

1. **A run under the wrong backend.** Every `run.json` names `llamacpp`, the 8002 base URL and the model. Pinned by Task 2's check.
2. **A run with different params.** The first request's sampling is checked per run. Pinned by Task 2.
3. **A record that outruns its evidence.** The README states counts and validity, and says what the run cannot claim. Pinned by Task 3.
4. **Raw evidence in git.** Only `run.json`, `final.md`, `brief.md`, `README.md` and `table.md` are added. Pinned by Task 3.
5. **Editing the preregistration after the fact.** A dated correction is allowed only as a new note; the original stands.

---

### Task 1: Preregister

**Files:**
- Create: `docs/superpowers/research/2026-10-20-llamacpp-reference-preregistration.md`

- [ ] **Step 1: Write the preregistration** with the question, backend, runner flags, n, validity check, reading and decision rule.
- [ ] **Step 2: Commit.** `git add docs/superpowers/research/2026-10-20-llamacpp-reference-preregistration.md docs/superpowers/plans/2026-10-20-lc3c-reference-run.md && git commit -m "docs(lc3c): preregister the llama.cpp reference run"`

---

### Task 2: Run it

**Files:**
- Create: `evals/baseline/2026-10-20-reference-llamacpp-rungs1-5/table.md`, `run.json` and `final.md`/`brief.md` per run

- [ ] **Step 1: Start the server.** `uv run scripts/backend.py start`, `status` says `up`.
- [ ] **Step 2: Run the preregistered command** from `ladder/`, with `--out ../evals/baseline/2026-10-20-reference-llamacpp-rungs1-5`.
- [ ] **Step 3: Check validity.** For each run, read `run.json`: `backend.provider == "llamacpp"`, base URL, model, worker version/git; read its trace's first `provider_request` and confirm `temperature 0`, `top_p 1`, `top_k 0`, `min_p 0`, `seed 42`, `max_tokens 4096`. Count passes per rung.
- [ ] **Step 4: Stop the server.**
- [ ] **Step 5: Commit** the tracked record files only (no `trace.jsonl`, `stdout.txt`, `diff.patch`).

---

### Task 3: Record and close

**Files:**
- Create: `evals/baseline/2026-10-20-reference-llamacpp-rungs1-5/README.md`
- Modify: `ROADMAP.md`, `docs/backends/llamacpp.md`, `CHANGELOG.md`

- [ ] **Step 1: Write the README.** Preregistration link, what is measured (backend, version, worker, n), the table of 15 rows, pass counts, validity, what it cannot claim, and the raw-evidence release line (tarball + SHA-256 when published, or "owed").
- [ ] **Step 2: Update the backend doc's Open list** and the changelog.
- [ ] **Step 3: Close the phase.** Status cell, `## Now`, `## Result`, archive this plan; run `npm test`, `node --test tests/docs-caps.test.mjs`.
- [ ] **Step 4: Commit** `docs: close LC.3C — the llama.cpp reference run`.

## Result

2026-10-20. Shipped: the preregistration and
`evals/baseline/2026-10-20-reference-llamacpp-rungs1-5/` (README, `table.md`, and each
run's `run.json`, `final.md`, `brief.md`).

Verified: 15/15 runs valid — every first request carried the greedy block and
`max_tokens` 4096; every record named `llamacpp`, the 8002 base URL and the
model; worker `v0.1.8-62-g16072e9`, prompt v5, `llama-server` 0.7.0.
**14/15 passed.** Rung 4 repeat 3 failed on `length` (8 requests, 1 tool
error, empty reply). The first invocation was interrupted by the agent's tool
timeout after rung 5 repeat 2; the missing repeat ran alone with identical
flags and is in the record, which says so.

Raw evidence (`trace.jsonl`, `stdout.txt`, `diff.patch`) is owed as
`reference-llamacpp-rungs1-5.tar.gz` on `research-2026-10-20`, with its
SHA-256, and stays out of git.
