---
phase: LC.3B
cycle: 1
lifecycle: closed
---

# LC.3B Ladder backend override implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `run_ladder` can point at llama.cpp with `--provider llamacpp --base-url http://127.0.0.1:8002/v1 --model llamacpp/Mellum2.1-12B-A2.5B-Thinking`, skip oMLX's admin API, and complete rung 1 against the local server. No measured claim is made.

**Architecture:** The runner's oMLX assumptions become parameters: `direct_agent_dir` writes whichever provider and model it is given, `build_pi_direct_args` takes the model, and `main` only opens the oMLX profile when the provider is `omlx`. The defaults stay oMLX, so every existing record's launch line still means what it says.

**Tech Stack:** Python 3.14 ladder (`uv run python -m ladder.run_ladder`), pytest under `ladder/`.

**Spec:** [Learning Center design](../specs/2026-10-20-learning-center-design.md) §4 (lesson 3), §6 (`reference-run`); `docs/sdd.md` "Measure what ships".

## Global Constraints

- Defaults are unchanged: `--provider omlx`, `--base-url http://127.0.0.1:8001/v1`, `--model omlx/Mellum2.1-12B-A2.5B-Thinking-6bit`, and the oMLX admin profile still applies and is verified for `omlx`.
- For any other provider, the runner must not call the oMLX admin API or `omlx --version`; it records the backend's own version instead.
- Request parameters stay the ladder's greedy values (`temperature 0`, `top_p 1`, `top_k 0`, `seed 42`) — the instrument's convention, not the lesson's sampling.
- The smoke runs rung 1, repeat 1, profile `baseline`, mode `direct`, and writes only to a scratch directory; it is **not** a `evals/` record and makes no claim.
- No scoring change. Every new test is shown failing first.

## Review Focus

1. **The oMLX path changing silently.** A default run must still write `provider: omlx`, port 8001 and the profile's request params. Pinned by Task 1's default-case test.
2. **A llama.cpp run calling the oMLX admin API.** With `--provider llamacpp`, no request goes to 8001 and no `omlx` binary is required. Pinned by Task 3.
3. **A model id split wrong.** `llamacpp/Mellum2.1-12B-A2.5B-Thinking` must become provider `llamacpp` and id `Mellum2.1-12B-A2.5B-Thinking` in `models.json` and in `--model`. Pinned by Tasks 1 and 3.
4. **A smoke becoming a claim.** No `evals/` directory, no badge upgrade, and the doc says "smoke". Pinned by Task 4.
5. **A profile applied without an admin API.** With `--provider llamacpp`, `main` must not construct the admin client or open `profile()`; the smoke must run with no `omlx` binary involved. Pinned by Task 4's smoke.

---

### Task 1: The direct profile takes a provider and model

**Files:**
- Modify: `ladder/ladder/pi_profile.py`
- Modify: `ladder/tests/test_pi_profile.py`

**Interfaces:**
- Produces: `direct_agent_dir(dest: Path, profile: str, base_url: str = "http://127.0.0.1:8001/v1", *, provider: str = "omlx", model_id: str = MODEL_ID, context_window: int = 56000) -> Path`; the provider key, `defaultProvider`, model `id` and `contextWindow` follow the arguments, and the request params stay `REQUEST_PARAMS[profile]`.

- [ ] **Step 1: Write the failing test.** In `test_pi_profile.py`, call `direct_agent_dir(tmp_path / "agent", "baseline", "http://127.0.0.1:8002/v1", provider="llamacpp", model_id="Mellum2.1-12B-A2.5B-Thinking", context_window=50000)` and assert `models.json` has exactly the `llamacpp` provider, that base URL, that model id and context window, and `settings.json`'s `defaultProvider`; a second test calls it with defaults and asserts `omlx`, `MODEL_ID` and 56000.
- [ ] **Step 2: Run and see them fail.** `cd ladder && uv run pytest tests/test_pi_profile.py -q` → FAIL, unexpected keyword.
- [ ] **Step 3: Implement the keyword-only parameters** with the current values as defaults; write the provider key and settings from them.
- [ ] **Step 4: Run and see them pass.** Same command → PASS.
- [ ] **Step 5: Commit.** `git add ladder/ladder/pi_profile.py ladder/tests/test_pi_profile.py && git commit -m "feat(lc3b): the ladder's direct profile takes a provider"`

---

### Task 2: The direct command takes the model

**Files:**
- Modify: `ladder/ladder/run_ladder.py`
- Modify: `ladder/tests/test_runner.py`

**Interfaces:**
- Produces: `build_pi_direct_args(..., model: str = MODEL)`; `--model` gets that value and nothing else changes.

- [ ] **Step 1: Write the failing test.** In `test_runner.py`, call `build_pi_direct_args("fix it", model="llamacpp/Mellum2.1-12B-A2.5B-Thinking")` and assert `args[args.index("--model") + 1]` is that string; a second test calls it without the argument and gets `MODEL`.
- [ ] **Step 2: Run and see them fail.** `uv run pytest tests/test_runner.py -q` → FAIL, unexpected keyword.
- [ ] **Step 3: Implement the parameter.**
- [ ] **Step 4: Run and see them pass.** Same command → PASS.
- [ ] **Step 5: Commit.** `git add ladder/ladder/run_ladder.py ladder/tests/test_runner.py && git commit -m "feat(lc3b): the direct command takes the model"`

---

### Task 3: The CLI takes a backend and skips oMLX's admin

**Files:**
- Modify: `ladder/ladder/run_ladder.py`, `ladder/tests/test_runner.py`

**Interfaces:**
- Produces: `--provider` (default `omlx`), `--base-url` (default `http://127.0.0.1:8001/v1`), `--model` (default `MODEL`); `run_once(...)` gains `provider`, `base_url` and `model`, and passes them to `direct_agent_dir` and `build_pi_direct_args`. `main` uses `contextlib.nullcontext({})` in place of `profile(...)` when the provider is not `omlx`, and records `versions["backend"]` from `llama-server --version` there.

- [ ] **Step 1: Write the failing tests.** `build_parser().parse_args(["--profile","baseline","--rung","1","--out",str(tmp_path)])` yields the oMLX defaults; adding the three flags yields the llama.cpp values; `model.split("/", 1)` gives the two halves the runner needs.
- [ ] **Step 2: Run and see them fail.** `uv run pytest tests/test_runner.py -q` → FAIL, unrecognized arguments.
- [ ] **Step 3: Implement** the flags, thread them through `run_once`, and branch the profile context on the provider. Update every `run_once` call site in the tests with the new keywords or defaults.
- [ ] **Step 4: Run and see them pass.** `uv run pytest -q` from `ladder/` → PASS.
- [ ] **Step 5: Commit.** `git add ladder && git commit -m "feat(lc3b): the ladder takes a backend"`

---

### Task 4: The rung-1 smoke on llama.cpp

**Files:**
- Modify: `docs/backends/llamacpp.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: the flags from Task 3 and the server from LC.2.

- [ ] **Step 1: Start the server.** `uv run scripts/backend.py start` from the repo root; `status` says `up`.
- [ ] **Step 2: Run the smoke.** From `ladder/`: `uv run python -m ladder.run_ladder --mode direct --profile baseline --rung 1 --repeat 1 --provider llamacpp --base-url http://127.0.0.1:8002/v1 --model llamacpp/Mellum2.1-12B-A2.5B-Thinking --out /tmp/lc3b-smoke`. Expected: the run completes, its table has one row, and the record shows provider requests from the llama.cpp port.
- [ ] **Step 3: Check it is not a claim.** `/tmp/lc3b-smoke` is outside `evals/`; no record lands in git.
- [ ] **Step 4: Write it down.** In `docs/backends/llamacpp.md` under Open: "A rung-1 smoke ran through the ladder (`--provider llamacpp --base-url …:8002`); it is a smoke, not a reference run." Add the changelog line for the three ladder flags.
- [ ] **Step 5: Commit.** `git add docs/backends/llamacpp.md CHANGELOG.md && git commit -m "docs(lc3b): the ladder can drive llama.cpp"`

---

## Verification

- `cd ladder && uv run pytest -q` passes, and `npm test` from the root still passes.
- The smoke's table shows `PASS` for rung 1 and no oMLX admin error.
- Nothing under `evals/` is added.

## Result

2026-10-20. Shipped on `lc3b`, unreleased: `--provider`, `--base-url`,
`--model` and `--context-window` on `run_ladder`; a direct profile written
for that provider; the oMLX admin profile skipped when the provider is not
`omlx`; and `run.json` naming the provider, base URL and model it measured.

Verified: `ladder/` pytest 183/183, `npm test` 346/346, docs caps. A rung-1
smoke on llama.cpp passed (7 requests, 0 tool errors, 8.8 s) and recorded
`llama-server` 0.7.0; the version had to come from stderr, and the backend
block was added after the first smoke showed neither was recorded. The smoke
wrote only to `/tmp`; no `evals/` record and no claim.
