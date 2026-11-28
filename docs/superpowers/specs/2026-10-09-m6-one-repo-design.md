# M.6 design: one repo — the ladder and its records move into mellum-worker

Date: 2026-10-09. Phase row: `ROADMAP.md` M.6 (added by this phase).
Decided with Paul in brainstorming, 2026-10-09:

- mellum-worker becomes the only public repo: the package, the ladder that
  measures it, and the records that justify its settings.
- mellum-mlx narrows to producing the Q6 MLX weights (conversion script,
  its tests, the quantization notes). Whether it goes private, and pruning
  it, are Paul's steps; this phase does not edit mellum-mlx.
- The readable research moves here; raw evidence (traces, stdout, diffs)
  goes into GitHub release assets on this repo.
- Serving notes split by purpose: notes that justify a setting this repo
  ships move here; notes about making the weights stay.
- Method: a snapshot copy with a provenance file, not a history import.

Nothing in this phase touches Mellum's request path (prompt, messages,
tools, sampling) or a guard's decision. It is not a measured change; the
one ladder launch is a smoke that proves the moved ladder works.

## Goal

1. `ladder/` in this repo runs the five-rung ladder against the extension,
   prompt and templates in this checkout, with no second copy to drift.
   This supersedes M.5 spec §3 (`--worker-root` in mellum-mlx).
2. Every phase record the README and recipe cite (A0–A17 and the earlier
   phases) is readable here, with its raw evidence one link away.
3. No tracked file depends on mellum-mlx except the provenance note and
   the pointer to where the weights are made.

## 1. What moves, and where

Source paths are in mellum-mlx at the commit recorded in
`evals/PROVENANCE.md`.

| From (mellum-mlx) | To (mellum-worker) | Notes |
| --- | --- | --- |
| `ladder/*.py`, `ladder/*.js`, `ladder/*.test.mjs`, `ladder/briefs/` | `ladder/ladder/` | the Python package, unchanged except §3 |
| `tests/test_{runner,sandbox,score,summarize,rescore,pi_profile,omlx_profiles,fixtures}.py`, `tests/fixtures_score/` | `ladder/tests/` | `test_conversion.py` stays |
| `conftest.py` | `ladder/conftest.py` | `collect_ignore = ["fixtures"]` |
| `fixtures/` (tracked files only, 140 KB; no `.venv`, `__pycache__`) | `ladder/fixtures/` | |
| `prompts/ablation/` | `ladder/prompts/ablation/` | v4a–v4c variants the records cite |
| `docs/research/ladder/<phase>/` | `evals/<phase>/` | readable files only, see §2 |
| `docs/research/ladder/ablation-summary.md` | `evals/ablation-summary.md` | |
| `docs/research/mellum-recovery-2026-10-07/` (and its `.zip`) | `docs/superpowers/research/2026-10-07-mellum-recovery/` | cited by the README |
| `docs/research/2026-10-07-mellum-omlx-native-cache.md` | `docs/superpowers/research/` | justifies the oMLX settings in the setup skill's step 3 |
| `docs/research/2026-10-07-mellum-independent-runtime.md` and `-evidence.json` | `docs/superpowers/research/` | backend research M.4 builds on |
| `docs/research/2026-10-09-worker-cost-options.md`, `2026-10-09-future-work.md` | `docs/superpowers/research/` | cited by the roadmap (M.7–M.9) |

Stays in mellum-mlx: `main.py` (conversion), `tests/test_conversion.py`,
`pyproject.toml`'s `mlx-lm` dependency, `2026-10-07-mellum-bf16-q6*`,
`2026-10-07-mellum-coreai.md`, `coreai-stage0/`, and its own README and
`docs/mellum-worker.md` (superseded by this repo's `docs/recipe.md`).

Moved research notes keep their dates and text. Each gets one line under
its title: "Moved from mellum-mlx on 2026-10-09; see
`evals/PROVENANCE.md`." Links inside them are rewritten by §4's
rules; nothing else in them is edited.

## 2. Phase records: readable here, raw in a release

Per run directory, these stay in git: `run.json`, `final.md`, `brief.md`.
Per phase: `README.md`, `table.md`. Never copied into git, archived
instead: `trace.jsonl`, `stdout.txt`, `diff.patch` (450 each, ~380 MB).

- One tarball per phase directory, `<phase>.tar.gz`, containing the raw
  files at their original relative paths, built by
  `ladder/scripts/archive_raw.py <phase dir> <out dir>` (stdlib `tarfile`).
- One GitHub release on this repo, tag `research-2026-10-09`, with every
  tarball attached. Creating it and uploading are outward-facing: the
  plan stops and asks Paul before `gh release create`.
- Each phase README gains a final line: "Raw traces, stdout and diffs:
  [`<phase>.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/<phase>.tar.gz)."
- `.gitignore` gains `evals/**/trace.jsonl`, `stdout.txt`,
  `diff.patch`, so new runs write them locally without committing them.
  Future phases attach their tarball to a new `research-YYYY-MM-DD`
  release; `docs/sdd.md` says so.
- `evals/PROVENANCE.md`: source repo, source commit SHA, date,
  the file list rules above, the release tag, and a SHA-256 per tarball.

Size check: the move adds about 4.5 MB to a clone (records ~4 MB, ladder
~0.2 MB, fixtures ~0.14 MB); a `pi install git:` clone today is ~0.5 MB.

## 3. The ladder in this repo

### Layout

```
ladder/
  pyproject.toml   uv project: requires-python >=3.14, no runtime deps, dev: pytest
  uv.lock
  conftest.py
  ladder/          the package (run_ladder, rungs, score, summarize, sandbox, pi_profile, ...)
  tests/
  fixtures/
  prompts/ablation/
  scripts/archive_raw.py
```

Run from `ladder/`: `uv run python -m ladder.run_ladder ...`;
`uv run python -m pytest` runs its tests. `npm test` does not run them
(its glob is `tests/*.test.mjs` at the repo root); the two JS tests that
moved with the package (`strip-thinking`, `thinking-budget`) run with
`node --test ladder/ladder/*.test.mjs`, added to `npm test`.

### Paths

In `ladder/ladder/run_ladder.py` and `pi_profile.py`, `ROOT` splits in two:
`LADDER_ROOT` (`ladder/`, for fixtures, briefs, ablation prompts) and
`REPO_ROOT` (its parent, the package). The worker's files come from
`REPO_ROOT`, always the checkout the ladder lives in:

- `PROMPT_FILE` = `prompts/mellum-worker.md`; `--prompt` still overrides,
  defaulting variants to `ladder/prompts/ablation/`.
- `MODE_EXT` = `extensions/mellum-mode.ts`; `GUARDS_EXT` =
  `extensions/mellum-guards.ts`.
- Mode runs pass `-e extensions/mellum-mode.ts -e <recorder>` and no guards
  file (shipped Mode runs the guard set itself; A17 ran this way). The
  mirrored operator profile drops any `packages` entry containing
  `mellum-worker` so the extension loads once:
  `mirror_agent_dir(..., exclude_packages=("mellum-worker",))` for mode
  runs only.
- `prepare_pi_workspace` renders the delegated agent file from
  `templates/pi/mellum-worker.agent.md`, replacing `{{MELLUM_WORKER_ROOT}}`
  with `REPO_ROOT` and appending the recorder to `subagentOnlyExtensions`.
  `sandbox.py` no longer copies a `.pi/` tree; the `.pi/` copies are not
  moved.
- `--out` defaults to `REPO_ROOT/evals/<name>`.
- Each `run.json` adds `worker_version` (from `package.json`) and
  `worker_git` (`git describe --always --dirty` in `REPO_ROOT`).
- `probe_mode_rpc.py` takes the same paths.

No `--worker-root` flag: to measure a tag, check it out in a worktree and
run that worktree's ladder.

### Tests (`ladder/tests/`)

Each new assertion is shown failing first (`docs/sdd.md`).

- `test_runner.py`: `PROMPT_FILE`, `MODE_EXT`, `GUARDS_EXT` resolve to
  existing files under `REPO_ROOT`; mode args carry the mode extension and
  the recorder and no guards path; direct args' guards path is
  `extensions/mellum-guards.ts`; `run.json` has `worker_version` equal to
  `package.json`'s version and a non-empty `worker_git`.
- `test_pi_profile.py`: `exclude_packages` drops only matching entries and
  keeps order; the rendered agent file's body equals the prompt and its
  `subagentOnlyExtensions` names `REPO_ROOT/extensions/mellum-guards.ts`
  and the recorder; no `.pi/mellum` is written.
- `test_fixtures.py`: unchanged, now pointing at `ladder/fixtures/`.
- `test_archive_raw.py`: a phase directory with raw and readable files
  yields a tarball holding exactly the raw ones at their relative paths.
- Moved tests that only change import paths need no failing-first step.

## 4. Rewiring this repo

- Every `mellum-mlx` link in tracked files is rewritten (86 references in
  11 files today):
  - `.../mellum-mlx/blob/main/docs/research/ladder/X` → `evals/X`
  - `.../mellum-mlx/blob/main/docs/research/<note>` → `docs/superpowers/research/<note>`
  - a note that stays in mellum-mlx (bf16-q6, CoreAI) → the HF model card
    `https://huggingface.co/pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit`
  - prose ("the research repo", "ablated in mellum-mlx") → "the ladder
    (`ladder/`)" and "the records (`evals/`)".
- `extensions/mellum-guards.ts`: its comment's citation becomes
  `evals/...`. Comment-only; no code change.
- `docs/sdd.md`: the standing rule reads "Measured settings are not
  changed without a ladder run in `ladder/`, recorded in `evals/`";
  the "Spec and plan in mellum-mlx" paragraph keeps its two links (history)
  but says the weights repo may go private and the M.1 design is
  summarized in `docs/recipe.md`. New: raw evidence goes in a
  `research-YYYY-MM-DD` release.
- `README.md`: "Measured, not guessed" and "Findings" point at
  `evals/ablation-summary.md` and the moved notes; the weights line
  names the HF repo. One sentence on running the ladder.
- `AGENTS.md`: the ladder's commands (`cd ladder && uv run python -m pytest`)
  and the rule that raw files are never committed.
- Guard test, `tests/docs.test.mjs` or a new `tests/no-mellum-mlx.test.mjs`:
  fails when a tracked file other than `evals/PROVENANCE.md`,
  `CHANGELOG.md` (history), and moved research notes' "moved from" line
  mentions `mellum-mlx`. The SDD records in `docs/superpowers/` written
  before this phase are history and may keep their mentions; the test's
  allowlist names that directory's pre-M.6 files explicitly.

## 5. Roadmap and M.5

- M.5 closes with its mellum-worker half (merged from branch
  `m5-print-mode-and-record`). Its §3 and the rung-1 smoke are superseded
  by M.6; its Status cell says so, its plan gets `## Result` and
  `lifecycle: closed`, and the backlog entries "The ladder measures the
  repo copy" and "Run-record consumers" are removed with M.5's row as
  their outcome.
- M.6 row added. The current M.6–M.8 (Worker one-liners, in-process
  Worker, mediated brief) become M.7–M.9; their "through M.5's
  `--worker-root`" wording becomes "through `ladder/`". M.3's
  "needs a `--harness opencode` runner in mellum-mlx" becomes "in
  `ladder/`".
- `## Now` points at this spec and the order: M.6, then M.7.

## 6. Order of implementation

1. Merge `m5-print-mode-and-record` into main (fast-forward or merge
   commit; suite green).
2. Copy §1's files; `ladder/pyproject.toml`, `uv.lock`, `.gitignore`;
   moved tests pass unchanged except import roots.
3. §3 paths and tests (TDD).
4. §2: `archive_raw.py` (TDD), build the tarballs from mellum-mlx's
   phase directories into a scratch directory (step 2 copied only the
   readable files), write `PROVENANCE.md` with their hashes, add the
   README link lines.
5. §4 rewiring and the guard test.
6. Smoke: `cd ladder && uv run python -m ladder.run_ladder --mode mode
   --profile baseline --rung 1 --repeat 1 --deadline 600 --out
   ../evals/2026-10-09-smoke-m6-one-repo`. Pass: the rung passes; requests in
   A17's rung-1 range (7–9); the first provider request has the v5 prompt
   as its only system message and seven tools; `run.json` has
   `worker_git`. Its README says one run proves the launch, not the rate.
7. §5 roadmap and M.5 close-out.
8. Stop for Paul: `gh release create research-2026-10-09` with the
   tarballs, then a check that every README link resolves (HTTP 200 on
   each asset URL). Push, the v0.1.3 bump and tag are Paul's.

Steps 3 and 4 are independent after 2; 6 needs 3; 8 needs 4.

## 7. Acceptance

- `npm test` green, including doc caps and the mellum-mlx guard test.
- `cd ladder && uv run python -m pytest` green.
- The smoke passes as in §6 step 6.
- `git ls-files | xargs du -ch` under 10 MB; no tracked `trace.jsonl`,
  `stdout.txt`, or `diff.patch`.
- Every phase README under `evals/` ends with its tarball link, and
  `PROVENANCE.md` lists a hash for each tarball.
- After Paul's release step: every tarball URL returns 200 and its hash
  matches `PROVENANCE.md`.

## 8. Excluded, and alternatives rejected

Excluded: any edit to mellum-mlx (going private, deleting its ladder,
its README); the HF model card text; any measured change; a
`--worker-root` flag; v0.1.3; rewriting the moved phase READMEs beyond the
raw-archive line and link rewrites.

Rejected:

- **History import** (`git filter-repo`/subtree): keeps blame on
  `ladder/`, but the 383 MB of raw files must be filtered out of history,
  which is fragile, and the phase records already date every result.
- **Leave records in a frozen mellum-mlx**: forces mellum-mlx to stay
  public for links to work, which is what Paul wants to end.
- **Commit the raw files here**: every `pi install git:` would clone
  ~68 MB of packs for evidence no user of the package reads.
- **A Hugging Face dataset for raw files**: a second public place.

## Risks

- The ladder's path assumptions are wider than §3 lists; the moved tests
  and the smoke are what catch it.
- A Pi or OpenCode host that installs from git might load files under
  `ladder/` (the JS recorders). Pi loads only `package.json`'s `pi.extensions`;
  OpenCode only its plugin entry. The smoke install check is to run
  `pi list` after `pi install` from a local path and confirm only the
  shipped extension loads; the plan includes it.
- Links in moved notes that point at mellum-mlx files that did not move
  (e.g. its `main.py`) become HF model card links or plain text, never
  dangling URLs into a repo that may go private.
