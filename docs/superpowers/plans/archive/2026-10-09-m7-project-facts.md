---
phase: M.7
cycle: 1
lifecycle: closed
---

# M.7 Project Facts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether a project facts block (forwarded by Mode) plus a `python -m pytest` fallback lets Mellum pass looser AgentClinic phase specs, and ship it only if the ladder says so.

**Architecture:** Four new ladder rungs (6–9) built from ac-demo's phases at a looser level, scored by hidden behaviour tests and a write-list check. A pure `readProjectFacts` in a new `extensions/mellum-facts.ts`; `filterForMellum` appends the facts to post-marker user messages in the outgoing payload only. Three measured phases (A18 off, A19 on, A20 fallback only) decide the ship.

**Tech Stack:** TypeScript extension run by Pi 1.0.2 (`node --test`), Python 3.14 ladder (uv, pytest), FastAPI fixture from ac-demo's lock, oMLX on `127.0.0.1:8001`.

**Spec:** `docs/superpowers/specs/2026-10-09-m7-project-facts-design.md` (Appendix A: the looser specs and facts block, verbatim; Appendix B: hidden tests).

## Global Constraints

- Never edit `/Users/pauleveritt/projects/pauleveritt/ac-demo/AGENTS.md`. If a step ever must, it restores it and checks `git -C /Users/pauleveritt/projects/pauleveritt/ac-demo diff --quiet AGENTS.md` before the step ends. No commits in ac-demo; probes use scratch clones.
- No change to `prompts/`, `templates/`, the worker tools, sampling, or guard decisions. Prompt stays v5.
- Facts section cap: 600 characters of bullets. Fallback command exactly `uv run --offline python -m pytest -q`. Switch: `MELLUM_MODE_FACTS=0`. Record field `facts: { source, testCommand, chars }`, sources `"agents-md" | "detected" | "agents-md+detected" | "none" | "off"`.
- Ship rule (spec §3): A19 rungs 1–5 ≥ 13/15; A19 rungs 6–9 ≥ A18 + 3 or ≥ 10/12; A19 median requests on 6–9 below A18's.
- Ladder runs never write to `~/.pi/agent/mellum-mode-runs.jsonl` (mode runs already set `MELLUM_MODE_RUNS` under scratch). Do not start, stop or reconfigure oMLX.
- Raw files never committed. Tarballs go to `/Users/pauleveritt/projects/pauleveritt/mellum-worker-raw-research-2026-10-09/` and PROVENANCE-style hashes into each phase README; the release (tag `research-2026-10-09`, not yet created) is Paul's step.
- `CHANGELOG.md` `[Unreleased]` entry in the same commit as any user-facing change (AGENTS.md rule); doc caps hold; every new assertion seen failing first.
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `m7-project-facts` in a worktree off `main`; no push, tag, release, version bump or merge to `main`.

## Review Focus

1. **AGENTS.md without the section, or with a `## Mellum` heading at the end of the file.** Parsing must end the section at EOF as well as at the next `#`/`##` heading, and ignore `###` sub-headings (Task 4 test).
2. **A user message whose content is an array with an image part.** Facts go into the last *text* part, or a new text part when there is none; never a crash (Task 4 test).
3. **`/mellum on` with several tasks.** Facts are appended to each task's message once per request, never accumulated across requests (Task 4 test: filter applied twice to the same payload copy yields one block per message).
4. **A fixture whose `uv sync --offline` fails** (cache missing). The fixture self-check must fail loudly rather than score every run as FAIL (Task 1 test runs the sync and asserts exit 0).
5. **Hidden test files colliding with Mellum's own files** (`_hidden_p1.py` already present). The scorer overwrites them only after the write-list check and reports a collision in `details` (Task 2 test).

---

### Task 1: AgentClinic fixture rungs 6–9

**Files:**
- Create: `ladder/fixtures/agentclinic-p1/`, `-p2/`, `-p3/`, `-p4/`, `ladder/fixtures/agentclinic-done/`, `ladder/fixtures/agentclinic-hidden/_hidden_p{1,2,3,4}.py`, `ladder/fixtures/agentclinic/README.md`
- Test: `ladder/tests/test_agentclinic_fixture.py`

**Interfaces:**
- Produces: fixture dirs where `agentclinic-pN` is the start of phase N and `agentclinic-done` has all four phases solved; hidden files named `_hidden_p<k>.py`.

- [ ] **Step 1: Common files.** Each fixture dir gets `pyproject.toml` and `uv.lock` from ac-demo HEAD (`git -C /Users/pauleveritt/projects/pauleveritt/ac-demo show HEAD:pyproject.toml`, same for `uv.lock`), `AGENTS.md` verbatim from spec Appendix A, a `.gitignore` with `.venv/`, `__pycache__/`, `.pytest_cache/`, and an empty `tests/` kept by `tests/.gitkeep` in `agentclinic-p1`.
- [ ] **Step 2: Specs.** `agentclinic-pN` holds `specs/phase-1-home.md` … `specs/phase-N-*.md` verbatim from Appendix A (the later phases are absent).
- [ ] **Step 3: Reference solutions.** Write a minimal, idiomatic solution of each phase that satisfies Appendix A (FastAPI + Jinja2Templates, dataclass `Complaint` with `field(default_factory=…)`, an `itertools.count` id, `RedirectResponse(status_code=303)`, Bootstrap 5 CDN), with the phase's own tests under `tests/` (`test_app.py`, `test_board.py`, `test_add.py`, `test_resolve.py`). `agentclinic-p2` = p1 files + phase 1 solution + phase 2 spec; and so on; `agentclinic-done` = all four solutions and specs.
- [ ] **Step 4: Hidden tests** in `agentclinic-hidden/`, exactly Appendix B's assertions, one file per phase, each building its own `TestClient(app)`.
- [ ] **Step 5: Write the failing self-check** `test_agentclinic_fixture.py`, marked `@pytest.mark.slow` (register the marker in `ladder/pyproject.toml` `[tool.pytest.ini_options] markers`). For each phase N: copy `agentclinic-pN` to `tmp_path`, `uv sync --offline` (assert exit 0, Review Focus 4), copy `_hidden_pN.py` in, and assert it FAILS; then copy the next state (`agentclinic-p(N+1)`, or `agentclinic-done` for N=4), sync, copy `_hidden_p1..N`, and assert they PASS together with `uv run --offline python -m pytest tests -q`. Run it before the reference solutions exist to see it fail.
- [ ] **Step 6:** Make it pass; `cd ladder && uv run python -m pytest -q` all green (the slow test included).
- [ ] **Step 7: Fixture README** `ladder/fixtures/agentclinic/README.md`: where it comes from (ac-demo HEAD SHA), the authoring rules (spec §2 and Appendix A's "what was dropped"), and a fact count per phase, original against looser (count one fact per bullet clause that states a requirement; show the counts and the percentage fewer). Commit `feat(ladder): AgentClinic rungs 6–9 fixtures, hidden tests and self-check` (no changelog entry: ladder internals only until Task 2 exposes the rungs).

### Task 2: Rungs 6–9 scoring and the runner switches

**Files:**
- Modify: `ladder/ladder/rungs.py`, `ladder/ladder/run_ladder.py`
- Test: `ladder/tests/test_rungs_agentclinic.py`, `ladder/tests/test_runner.py`

**Interfaces:**
- Consumes: Task 1 fixtures.
- Produces: `RUNGS[6..9]`; `outside_write_list(ws: Path, allowed: tuple[str, ...]) -> list[str]`; `check_agentclinic(phase: int) -> Callable[[Path, Path], CheckResult]` with `details` keys `facts_cmd_pass`, `hidden_pass`, `outside_write_list`, `hidden_collision`; `prepare_workspace(rung, scratch, strip_facts_section: bool = False)`; `strip_mellum_section(text: str) -> str`; CLI flags `--mode-facts {on,off}` (default `on`) and `--strip-facts-section`; `mode_env(..., facts: bool = True)` sets `MELLUM_MODE_FACTS=0` when `facts` is false; `run.json` keys `mode_facts`, `strip_facts_section`.

- [ ] **Step 1: Write failing tests.**
  - `outside_write_list`: in a git-initialised tmp dir with a baseline commit, new `app.py`, `templates/x.html`, `tests/test_y.py` are allowed; new `pytest.ini`, `__init__.py` and a modified `pyproject.toml` are returned, sorted; ignored `.venv/` is not.
  - `strip_mellum_section`: removes `## Mellum` through the line before the next `#`/`##` heading or EOF, keeps the rest byte-for-byte; a file without the section is unchanged.
  - `check_agentclinic(N)` on a copy of the next state (as in Task 1) passes with `outside_write_list == []`; on an unchanged copy of `agentclinic-pN` it fails with `hidden_pass False`; a workspace with an extra `pytest.ini` fails with it listed; a workspace already holding `_hidden_p1.py` reports `hidden_collision: ["_hidden_p1.py"]` (Review Focus 5).
  - `RUNGS[6].sentence == "Implement specs/phase-1-home.md"`, `RUNGS[9].sentence == "Implement specs/phase-4-resolve-reopen.md"`, fixtures `agentclinic-p1` … `p4`.
  - `mode_env(..., facts=False)["MELLUM_MODE_FACTS"] == "0"`; with `facts=True` the key is absent.
- [ ] **Step 2:** Run; expect ImportError/AttributeError failures. Record them in Progress.
- [ ] **Step 3: Implement.** `check_agentclinic(phase)` returns a check that: (1) computes `outside_write_list(ws, ("app.py", "models.py", "templates/", "tests/"))` from `git status --porcelain --untracked-files=all`; (2) records which `_hidden_p*.py` already exist, then copies `_hidden_p1..phase` in; (3) runs `["uv","run","--offline","python","-m","pytest","tests","-q"]` (facts command, offline) and `["uv","run","--offline","python","-m","pytest", *hidden, "-q"]`; (4) `tests_unchanged` = every file under the fixture's `tests/` is byte-identical in `ws`; passed = all four and no outside paths. Rung test_cmd is the facts command list. `prepare_workspace` strips the section from `ws/AGENTS.md` before the baseline commit when asked. Wire the two CLI flags through `run_once` into `mode_env` and the record.
- [ ] **Step 4:** Tests pass; full ladder suite green. Commit `feat(ladder): rungs 6–9 (AgentClinic phases), write-list scoring, facts switches` with a CHANGELOG `[Unreleased]` "Added" line.

### Task 3: A18 — baseline, Mode with facts off

**Files:** Create `evals/2026-10-09-ablation-a18-agentclinic-facts-off/README.md` and its readable run files; modify `evals/ablation-summary.md`.

- [ ] **Step 1:** oMLX check: `curl -s -m 3 http://127.0.0.1:8001/v1/models` lists `Mellum2.1-12B-A2.5B-Thinking-6bit`, else stop and report. Note `wc -l ~/.pi/agent/mellum-mode-runs.jsonl`.
- [ ] **Step 2:** From `ladder/`, in the background with a log (each run can take minutes; poll the table, do not block the tool): `nohup uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 6 --rung 7 --rung 8 --rung 9 --repeat 3 --deadline 600 --mode-facts off --out ../evals/2026-10-09-ablation-a18-agentclinic-facts-off < /dev/null > /tmp/a18.log 2>&1 &`. Expect 12 rows in `table.md`.
- [ ] **Step 3:** README in the existing phase-README shape (look at `evals/2026-10-09-ablation-a17-mode-v012/README.md`): launch, passes per rung, median requests per rung, `outside_write_list` per run (from each `run.json`'s `check.details`), wall, notes on failure shapes. Archive raw files with `uv run python -m ladder.archive_raw --out /Users/pauleveritt/projects/pauleveritt/mellum-worker-raw-research-2026-10-09 --tag research-2026-10-09 ../evals/2026-10-09-ablation-a18-agentclinic-facts-off/` and add the link and hash lines. Add an A18 row to `ablation-summary.md`. Run log line count unchanged.
- [ ] **Step 4:** `git status` shows no raw files staged. Commit `docs(ladder): A18 — AgentClinic rungs with facts off (baseline)` with a CHANGELOG line.

### Task 4: Mode reads and forwards project facts

**Files:**
- Create: `extensions/mellum-facts.ts`, `tests/mellum-facts.test.mjs`
- Modify: `extensions/mellum-mode.ts` (`filterForMellum`, `activate`, `summaryLine`/`collapseHandoffs`, `RunRecord`/`runRecord`, the request hook), `tests/mellum-mode.test.mjs`, `tests/mellum-mode-hooks.test.mjs`, `docs/recipe.md` §4b, `CHANGELOG.md`

**Interfaces:**
- Produces: `export type FactsSource = "agents-md" | "detected" | "agents-md+detected" | "none" | "off"`; `export interface ProjectFacts { source: FactsSource; bullets: string[]; testCommand: string | null; chars: number; warning?: string }`; `export function readProjectFacts(dir: string, io: { read(path: string): string | undefined }, env?: Record<string, string | undefined>): ProjectFacts`; `export function factsBlock(f: ProjectFacts): string` (empty string when no bullets, else `"\n\nProject facts:\n- " + bullets.join("\n- ")`); `filterForMellum(payload, systemPrompt, opts: { expectMarker?: boolean; facts?: string })`; on-marker content becomes `` `${MARK_ON} facts: ${source}` ``.

- [ ] **Step 1: Write failing tests** in `tests/mellum-facts.test.mjs` (import from `../extensions/mellum-facts.ts` the way `tests/mellum-commands.test.mjs` imports its module). Cases with an in-memory `io`:
  - Appendix A's `AGENTS.md` → `source "agents-md"`, three bullets without the `- `, `testCommand "uv run python -m pytest tests"`, `chars` = sum of bullet lengths.
  - section followed by `## Other` and by EOF; a `### Notes` inside the section is part of it but contributes only its bullets (Review Focus 1).
  - section without a test bullet + `pyproject.toml` containing `pytest` → `"agents-md+detected"`, last bullet `Test command: uv run --offline python -m pytest -q`.
  - no `AGENTS.md`, pytest pyproject → `"detected"`; no `AGENTS.md`, only `package.json` → `"none"`, no bullets.
  - bullets over 600 chars → `warning` set, section ignored, fallback applies.
  - `env.MELLUM_MODE_FACTS === "0"` → `"off"`, no bullets even with a section.
  - `factsBlock` of none is `""`.
  In `tests/mellum-mode.test.mjs` for `filterForMellum` with `facts`: appended to each post-marker user message with string content; with array content, to the last text part, or a new text part after an image-only part (Review Focus 2); not to `tool` messages or pre-marker messages; applying the filter to the same input twice yields exactly one block per message (Review Focus 3); empty `facts` leaves the payload as before. In `tests/mellum-mode-hooks.test.mjs`: the record line carries `facts`, the on-marker carries `facts: <source>`, and the handoff summary line contains `facts: <source>`.
- [ ] **Step 2:** Run `npm test`; the new tests fail (missing module, missing behaviour). Record in Progress.
- [ ] **Step 3: Implement** `mellum-facts.ts` as specified (section starts at a line matching `/^##\s+Mellum\s*$/i`, ends before the next line matching `/^#{1,2}\s/` or at EOF; bullets are lines matching `/^\s*[-*]\s+(.+)$/`; test command from a bullet matching `/^test command:\s*(.+)$/i`; fallback when no test command and `pyproject.toml` matches `/pytest/`). In `mellum-mode.ts`: `activate` calls `readProjectFacts(process.cwd(), { read: p => existsSync(p) ? readFileSync(p, "utf8") : undefined })`, stores it for the span, warns via the existing `warn` helper on `warning`, and puts the source in the on-marker; the request hook passes `facts: factsBlock(spanFacts)`; `filterForMellum` appends to copies of kept user messages (never mutating the input); `collapseHandoffs` reads `facts: (\S+)` from the span's on-marker and `summaryLine` appends `, facts: <source>` when present; `runRecord` adds `facts: { source, testCommand, chars }` from `RecordMeta.facts`.
- [ ] **Step 4:** `npm test` green. Recipe §4b gets a paragraph: the section, the cap, the fallback, `MELLUM_MODE_FACTS=0`, and that it is not yet shipped advice until A19. CHANGELOG `[Unreleased]` "Added" line. Commit `feat(mode): forward the project's ## Mellum facts and a python -m pytest fallback`.

### Task 5: A19 and A20, the ship decision, the research note

**Files:** Create `evals/2026-10-10-ablation-a19-facts-on/`, `evals/2026-10-10-ablation-a20-facts-fallback-only/`, `docs/superpowers/research/2026-10-09-m7-project-facts.md` (+ evidence dir); modify `evals/ablation-summary.md`.

- [ ] **Step 1:** oMLX check and run-log count as in Task 3. A19: same command shape with `--rung 1` … `--rung 9 --repeat 3 --mode-facts on --out ../evals/2026-10-10-ablation-a19-facts-on` (27 runs). Then A20: `--rung 6` … `--rung 9 --repeat 3 --strip-facts-section --out ../evals/2026-10-10-ablation-a20-facts-fallback-only` (12 runs). Background with logs, polled.
- [ ] **Step 2:** READMEs, archives, hashes and summary rows as in Task 3. Each README states the A17/A18 comparison it answers.
- [ ] **Step 3: Decide.** Apply the ship rule from Global Constraints literally and write the verdict with the numbers into the research note: honesty header (What is measured / What is conjecture), the phase-1 probe evidence (copy `/private/tmp/claude-501/-Users-pauleveritt-projects-pauleveritt-mellum-worker/a6d84638-af5f-4638-99a2-5f712fa04072/scratchpad/briefs/runs.jsonl` into the evidence dir if it still exists; otherwise cite the spec's table), A18/A19/A20 per rung, `outside_write_list` counts, A20's share of the gain, What would falsify this, Risks.
- [ ] **Step 4:** Commit `docs(ladder): A19 and A20 — project facts on and fallback only; verdict` with a CHANGELOG line.

### Task 6: Ship or hold; backlog and roadmap

**Files:** Modify `README.md`, `skills/mellum-setup/SKILL.md` (+ a new `skills/mellum-setup/reference/` step file), `BACKLOG.md`, `ROADMAP.md`, `CHANGELOG.md`; tests as the skill's structure test requires.

- [ ] **Step 1 (if A19 ships):** README "Use it": one paragraph and Appendix A's three-bullet example; without the section, Python projects get `python -m pytest`; `MELLUM_MODE_FACTS=0` turns it off. Setup skill: an optional step "Project facts" that, in the current project, asks for the test command (and offers the write-only and do-not lines), shows the section, and asks before appending it to `AGENTS.md`; follow the existing step-file pattern and keep `tests/skill.test.mjs` green (extend it if it enumerates steps). Recipe §4b loses "not yet shipped".
- [ ] **Step 1 (if A19 fails):** `git revert` Task 4's commit(s) on the branch (fixture, switches, A18–A20 records and the research note stay); recipe paragraph removed by the revert; the note says why.
- [ ] **Step 2: Backlog.** Add "Write-only guard: refuse writes outside the facts block's list" (reopens when a facts-on phase shows `outside_write_list` violations; cite the A19 count). If shipped, remove "Mode and the project's AGENTS.md" and "Mode-side test-command preflight"; narrow "Prompt default `python -m pytest`" to Worker. If held, update those entries' text with the verdict instead.
- [ ] **Step 3: Roadmap.** Add the M.7 row (Ships/Excludes from the spec; Status with the verdict and links, within caps). Renumber Worker one-liners, in-process Worker, mediated brief to M.8, M.9, M.10; M.10's Status says it compares on rungs 6–9 against A18/A19. `## Now`: M.7 result, next M.8.
- [ ] **Step 4:** CHANGELOG checkpoint against `git log v0.1.2..HEAD --oneline`. `npm test` and ladder pytest green. Commit `docs: M.7 verdict on the roadmap and backlog` (+ the ship-gated docs commit if shipped, separately: `docs: project facts in the README and the setup skill`).

### Task 7: ac-demo copy and close-out

**Files:** Create in ac-demo (uncommitted): `specs/loose/phase-{1-home,2-board,3-add,4-resolve-reopen}.md`. Modify this plan.

- [ ] **Step 1:** `git -C /Users/pauleveritt/projects/pauleveritt/ac-demo status --short` and record it. Copy the four looser specs from `ladder/fixtures/agentclinic-done/specs/` to ac-demo `specs/loose/`. Confirm `git -C … diff --quiet AGENTS.md` and that the only status change is the new `specs/loose/` directory.
- [ ] **Step 2:** In this plan: Progress filled per task (failing-first evidence, run counts, verdict), and a final note listing for Paul: the `## Mellum` section to paste into ac-demo's `AGENTS.md` (Appendix A's three bullets), the release step for the new tarballs, and the merge. Leave `lifecycle: active` until Paul merges; commit `docs(plan): M.7 progress`.

## Progress

Verdict: **SHIP**. Ledger with the rulings: `.superpowers/sdd/2026-10-09-m7-project-facts/progress.md`.

- **Task 1** (`94cd7ff`): AgentClinic fixtures p1..p4 and done, hidden tests, self-check. Failing first: self-check written before the fixtures, `9 failed` (missing directories and hidden files). Ladder pytest 91 passed; `npm test` 102 pass.
- **Task 2** (`6879db8`, fix `38a4e64`): rungs 6–9, write-list scoring, `--mode-facts` and `--strip-facts-section`. Failing first: ImportError on the new rung and check functions; the review round saw the switch-wiring test fail with the wiring broken (`assert None == '0'`, 4 failed) and the write-list check fail open (`[] != ['<git status failed>']`), then closed both. Ladder pytest 123 passed.
- **Task 3** (`ac04bdc`, fix `ef07e59`): A18, facts off, 12 runs (rungs 6–9 x 3), 20:15–21:19 on 2026-10-09: strict 0/12, median requests 50 over all 12 runs (per rung 42 / 42 / 57 / 51). No write to `~/.pi/agent` (run log stayed at 7 lines).
- **Task 2b** (`6a869b8`, inserted before Task 4, Paul's rule change for rule 3 on 2026-10-09 after A18 7 r1 failed only for an appended test): rungs 6–9 now require that no existing test is removed or edited, and additions are allowed; rungs 1–5 unchanged. Failing first: 11 failed with a stub of the strict rule (appended test, `.gitkeep` removal and five rescore cases); edited, deleted and renamed cases are tightening-only and pass under the strict rule. Ladder pytest 146 passed. A18 rescored with `ladder.rescore`: **1/12** (strict 0/12); both scorings are in its README.
- **Task 4** (`aff031a`): `extensions/mellum-facts.ts` parses `## Mellum` (600-character cap, `MELLUM_MODE_FACTS=0`, fallback `uv run --offline python -m pytest -q`), Mode forwards it with each kept user message, the on-marker names the source. Failing first: `npm test` `119 tests / 103 pass / 16 fail` (module missing, 8 hook and 7 mode tests). After: 134 pass.
- **Task 5** (`4ea9bc7`, fix `4885e12`): A19 (facts on, 27 runs) and A20 (fallback only, 12 runs). Paul paused on 2026-10-09 21:41; A19 stood at 4 rows and was stopped, moved (not deleted) to the session scratchpad, and re-run from scratch on 2026-10-10 08:10. A19: rungs 1–5 **15/15**, rungs 6–9 **9/12**, median requests 26. A20 (`--strip-facts-section`): **7/12**, median 28. Run log still 7 lines after both. Review fix round: leftover deadline servers recorded, A17 nudge count corrected, a false spread claim replaced by numbers. `npm test` 134 pass.
- **Verdict numbers** (spec §3): A19 rungs 1–5 15/15 against ≥ 13; rungs 6–9 9/12 against A18 rescored 1/12 + 3; median requests on 6–9, 26 against A18's 50. All three pass, so SHIP.
- **Task 6** (`bb6b256`, `2e97fc4`, fix `840bcce`): README, recipe, setup skill step 08, CHANGELOG, ROADMAP and BACKLOG carry the verdict. Failing first: the skill-step test (step file and link absent), and in the fix round a test that the step's check is the anchored `^## Mellum$` (it first matched phase 6's `## Mellum Worker`). `npm test` 135 pass.
- **Harness findings** (backlog, both reopen on the next ladder change): A20 9 r1's shell inherited the ladder's venv on PATH and pip-installed into `ladder/.venv` (restored with `uv sync --exact --offline`; scores used each workspace's own venv), in the backlog entry "Ladder PATH leaks its venv into Mellum's shell"; and deadline-cut runs left workspace servers running, which contaminated A19 8 r2 and A20 6 r2, in "Deadline leaves workspace servers running". The leftovers were stopped by hand.
- **Task 7**: the four looser specs were copied byte-for-byte (`cmp` clean) to ac-demo `specs/loose/`, uncommitted; ac-demo `AGENTS.md` untouched.

### For Paul

1. Paste this section into ac-demo's `AGENTS.md` (Appendix A's bullets; I did not touch that file):

```markdown
## Mellum

- Test command: uv run python -m pytest tests
- Write only: app.py, models.py, templates/, tests/
- Do not: install packages or add dependencies; remove or rewrite routes that already work; weaken tests
```

2. Release: publish the new tarballs `ablation-a18-agentclinic-facts-off`, `ablation-a19-facts-on` and `ablation-a20-facts-fallback-only` from `/Users/pauleveritt/projects/pauleveritt/mellum-worker-raw-research-2026-10-09/` as release `research-2026-10-09`.
3. Merge `m7-project-facts` into `main`. `main` has since gained `1c12d2c`, which also appends to the end of `BACKLOG.md`, so expect an add/add conflict there; keep both entries. Then finish the phase per AGENTS.md (Status cell, `## Result`, archive the plan).

## Result

2026-10-10. Shipped in v0.1.3; verdict SHIP under the literal rule. A19
rungs 1–5 15/15; rungs 6–9 9/12 against A18's 1/12 (rescored under Paul's
added-tests rule; 0/12 strict); median requests 26 against 50. A20
(fallback only) 7/12, median 28. `outside_write_list` 8/12 → 0/12. Tarballs
for A18–A20 are in release `research-2026-10-09` (34 assets, hashes
verified). Before the tag, one RPC probe on rung 6's fixture showed the
interactive marker `facts: agents-md` and a schema-2 record with
`facts.source: agents-md`; tests passed. Merged to `main` with an add/add
`BACKLOG.md` conflict resolved by keeping both sides. Suites at close:
`npm test` 135, ladder pytest 146.
