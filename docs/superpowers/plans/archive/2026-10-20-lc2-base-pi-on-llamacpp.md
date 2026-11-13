---
phase: LC.2
cycle: 1
lifecycle: closed
---

# LC.2 Base Pi on llama.cpp implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A learner with no Python clones this repo, installs `uv`, starts llama.cpp through one Python command whose settings come from `pyproject.toml`, and gets an answer from base Pi through a private profile; maintainers get `learn/project/` explaining the arrangement.

**Architecture:** `[tool.mellum]` in the root `pyproject.toml` is the only source of model settings. `scripts/backend.py` (stdlib only) reads it to launch `llama-server`, chat, and generate `learn/code/profile/models.json`; a drift test keeps the generated profile honest. The lesson and the project pages are plain Markdown in `learn/`, checked by `tests/learn-site.test.mjs`.

**Tech Stack:** Python 3.14 through `uv` (`tomllib`, `urllib`, `subprocess` only), Node's test runner, Zensical.

**Spec:** [Learning Center design](../specs/2026-10-20-learning-center-design.md) §4, §7, §12.

## Global Constraints

- `[tool.mellum]`: `model = "JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M"`, `context = 50000`, `max_tokens = 16384`, `temperature = 1.0`, `top_p = 0.95`, `top_k = 20`.
- Host `127.0.0.1`, port `8002`; extra `llama-server` flags `-np 1 -ngl 99 --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0`, and model alias `-a Mellum2.1-12B-A2.5B-Thinking`.
- Pi runs with `PI_CODING_AGENT_DIR` plus `--no-extensions --no-skills --no-prompt-templates --no-themes --no-context-files --no-session --no-approve`; nothing reads or writes `~/.pi`.
- No npm `build`, `prepare`, `prepack` or `install` script. Every new test is shown failing first.
- Docs caps stay: spec 400 lines, roadmap Ships/Excludes 900 chars, Status 1,000.
- macOS is the tested lane; Linux and Windows use llama.cpp's releases and the same commands.
- `[Unreleased]` gains its entry in the commit that changes what a learner or maintainer reads.

## Review Focus

1. **No Python on the machine.** `uv run` must fetch 3.14 from the root pyproject before `scripts/backend.py` imports; lesson 1's order is the guarantee. Pinned by Task 1's test and Task 5's page test.
2. **A hand-edited `models.json`.** The drift test must fail rather than let Pi sample differently from `chat`. Pinned by Task 3.
3. **`llama-server` missing.** `start` exits non-zero with "not found on PATH" and the doc link, writes no pidfile, and prints no traceback. Pinned by Task 4.
4. **A learner's existing `~/.pi`.** The lesson's command sets `PI_CODING_AGENT_DIR` and the `--no-*` flags, so nothing loads from it. Pinned by Task 5's page test.
5. **Port 8002 already serving.** `start` reports "already up" and does not spawn a second server. Pinned by Task 4.

---

### Task 1: Root pyproject and the settings it holds

**Files:**
- Create: `pyproject.toml`
- Test: `tests/backend-config.test.mjs`

**Interfaces:**
- Produces: `[project] requires-python = ">=3.14"`, `[tool.uv] package = false`, and the six `[tool.mellum]` keys in Global Constraints. Tasks 2–4 read them with `tomllib`; Task 7's doc names them.

- [ ] **Step 1: Write the failing test.** `tests/backend-config.test.mjs` asserts the file carries `requires-python = ">=3.14"` and each `[tool.mellum]` value from Global Constraints, with one failure message per missing line.

- [ ] **Step 2: Run it and see it fail.** `node --test tests/backend-config.test.mjs` → FAIL, `ENOENT` on `pyproject.toml`.
- [ ] **Step 3: Write `pyproject.toml`** with `[project] name = "mellum-worker-learning-center"`, `version = "0.0.0"`, the description "Learner workspace for the Mellum Learning Center", `requires-python = ">=3.14"`; `[tool.uv] package = false`; and the six values above under `[tool.mellum]`.
- [ ] **Step 4: Run it and see it pass.** Same command → PASS 1/1.
- [ ] **Step 5: Commit.** `git add pyproject.toml tests/backend-config.test.mjs && git commit -m "feat(lc2): root pyproject with the model settings"`

---

### Task 2: `serve` and `chat` built from the settings

**Files:**
- Create: `scripts/backend.py`
- Test: `tests/backend-cli.test.mjs`

**Interfaces:**
- Consumes: `[tool.mellum]` from Task 1.
- Produces: `load_settings(root: Path) -> dict`, `serve_argv(settings: dict, host: str = "127.0.0.1", port: int = 8002, binary: str = "llama-server") -> list[str]`, `chat_body(settings: dict, prompt: str) -> dict`; CLI `serve [--dry-run]`, `chat PROMPT [--dry-run]`. Task 3 adds `profile_models(settings)`; Task 4 adds `start`, `stop`, `status`.

- [ ] **Step 1: Write the failing test.** Run `uv run scripts/backend.py serve --dry-run` and assert the argv is exactly `["llama-server", "-hf", "<model>", "-a", "Mellum2.1-12B-A2.5B-Thinking", "--host", "127.0.0.1", "--port", "8002", "-c", "50000", "-np", "1", "-ngl", "99", "--jinja", "-fa", "auto", "-b", "512", "-ub", "512", "-ctk", "q8_0", "-ctv", "q8_0"]`; run `uv run scripts/backend.py chat "hi" --dry-run` and assert the parsed body is `{"messages":[{"role":"user","content":"hi"}],"max_tokens":16384,"temperature":1.0,"top_p":0.95,"top_k":20}`. Spawn with `spawnSync("uv", ["run", "scripts/backend.py", ...], { encoding: "utf8" })` and assert `status === 0`.
- [ ] **Step 2: Run it and see it fail.** `node --test tests/backend-cli.test.mjs` → FAIL, `scripts/backend.py` missing.
- [ ] **Step 3: Implement `scripts/backend.py`.** Use `argparse`; locate the repo root as `Path(__file__).resolve().parent.parent`; read `pyproject.toml` with `tomllib` and return `data["tool"]["mellum"]`. `serve --dry-run` prints `shlex.join(serve_argv(...))`; `chat --dry-run` prints `json.dumps(chat_body(...))`. Non-dry runs: `serve` execs the argv, `chat` POSTs to `http://host:port/v1/chat/completions` with `urllib.request` and prints the reply, sending `[thinking]`/token lines to stderr as `chat` did before.
- [ ] **Step 4: Run it and see it pass.** Same command → PASS 2/2.
- [ ] **Step 5: Commit.** `git add scripts/backend.py tests/backend-cli.test.mjs && git commit -m "feat(lc2): a stdlib backend CLI with serve and chat"`

---

### Task 3: One generated Pi profile

**Files:**
- Create: `learn/code/profile/models.json`
- Modify: `scripts/backend.py` (add `profile_models` and the `profile` command)
- Test: `tests/backend-profile.test.mjs`

**Interfaces:**
- Consumes: `load_settings` from Task 2.
- Produces: `profile_models(settings: dict) -> dict` and `profile [--dry-run]`, which writes `learn/code/profile/models.json` as `json.dumps(profile_models(settings), indent=2) + "\n"`. The provider is `llamacpp`, base URL `http://127.0.0.1:8002/v1`, model id `Mellum2.1-12B-A2.5B-Thinking`, `contextWindow` and `maxTokens` from settings, `samplingParams` `{temperature, top_p, top_k, min_p: 0, presence_penalty: 0, repetition_penalty: 1}`, and the oMLX compat block (`supportsDeveloperRole: false`, `supportsReasoningEffort: false`, `maxTokensField: "max_tokens"`, `thinkingFormat: "qwen-chat-template"`).

- [ ] **Step 1: Write the failing test.** `uv run scripts/backend.py profile --dry-run` must print exactly the committed `learn/code/profile/models.json`; parse the file and assert `providers.llamacpp.baseUrl`, `.models[0].id`, `.contextWindow === 50000`, `.maxTokens === 16384`, and the three sampling values. Use one test per assertion group, `readFileSync` plus `spawnSync` as in Task 2.
- [ ] **Step 2: Run it and see it fail.** `node --test tests/backend-profile.test.mjs` → FAIL, `models.json` missing.
- [ ] **Step 3: Implement `profile_models` and `profile`.** Then run `uv run scripts/backend.py profile` once to write the file, and read it to confirm the shape.
- [ ] **Step 4: Run it and see it pass.** Same command → PASS.
- [ ] **Step 5: Commit.** `git add learn/code/profile/models.json scripts/backend.py tests/backend-profile.test.mjs && git commit -m "feat(lc2): generate the private Pi profile from the settings"`

---

### Task 4: `start`, `stop` and `status`, with actionable failures

**Files:**
- Modify: `scripts/backend.py`
- Test: `tests/backend-lifecycle.test.mjs`

**Interfaces:**
- Produces: `health(host: str, port: int) -> dict | None` (GET `/health`, `None` when nothing answers); subcommands `start`, `stop`, `status`, each accepting `--host`, `--port`, `--pidfile` (default `tempfile.gettempdir()/llamacpp-mellum.pid`) and `--logfile`; `start` also accepts `--server-binary` (default `llama-server`). `start` prints `already up on <host>:<port> (pid <n>)` and exits 0 when `/health` answers; otherwise it spawns `serve_argv(...)` with output to the logfile, writes the pidfile, and waits up to 900 s for health, because the first start downloads the Q4_K_M weights. `stop` terminates the pidfile's process, or prints `not running`. A start whose binary is missing exits 2 with `llama-server not found on PATH; install it: docs/backends/llamacpp.md` and writes no pidfile.

- [ ] **Step 1: Write the failing test.** Start a `node:http` server on port 0 whose `/health` answers `{"status":"ok"}` and whose `/props` answers `{"default_generation_settings":{"n_ctx":50000}}`. Then: `status --port <p>` exits 0 and stdout contains `up on 127.0.0.1:<p>` and `50000`; `start --port <p> --pidfile <tmp>` exits 0, prints `already up`, and leaves the pidfile absent; `status --port <closed>` prints `down on`; `start --server-binary /nonexistent --pidfile <tmp> --logfile <tmp>` exits non-zero, writes no pidfile, and its stderr contains `not found on PATH`. Close the server in `after`.
- [ ] **Step 2: Run it and see it fail.** `node --test tests/backend-lifecycle.test.mjs` → FAIL, `start` is not a command.
- [ ] **Step 3: Implement the three subcommands** with `subprocess.Popen`, `urllib` health polling, `os.kill(pid, 0)` liveness, and `SystemExit` messages; catch `FileNotFoundError` before writing the pidfile.
- [ ] **Step 4: Run it and see it pass.** Same command → PASS 4/4.
- [ ] **Step 5: Commit.** `git add scripts/backend.py tests/backend-lifecycle.test.mjs && git commit -m "feat(lc2): start, stop and status with clear failures"`

---

### Task 5: Lesson 1

**Files:**
- Create: `learn/getting-started/base-pi-on-llamacpp.md`
- Modify: `learn/getting-started/index.md`, `zensical.toml`, `tests/learn-site.test.mjs`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `uv run scripts/backend.py start|chat|status`, `[tool.mellum]`, `learn/code/profile/`.
- Produces: front matter `title: Base Pi on llama.cpp`, `track: getting-started`, `position: 1`, `prerequisites: []`, `authors: [Paul Everitt]`, `backends: [llamacpp]`.

- [ ] **Step 1: Write the failing test.** Add the page to `PAGES` and to the nav check; add one test asserting the page's front matter has `track: getting-started` and that its body contains, in this order and case-insensitively, `install uv`, `pyproject.toml`, `uv run scripts/backend.py start`, `uv run scripts/backend.py chat`, `uv run scripts/backend.py stop`, `uvx ruff`, `PI_CODING_AGENT_DIR`, `--no-extensions`, `--no-context-files`, `learn/code/profile`; and that `learn/getting-started/index.md` links `base-pi-on-llamacpp.md` and no longer says "coming".
- [ ] **Step 2: Run it and see it fail.** `node --test tests/learn-site.test.mjs` → FAIL, page missing.
- [ ] **Step 3: Write the page.** Sections: what the lesson produces; install `uv` (the installer command per platform); "Why a `pyproject.toml`" (no Python on the machine, `uv` reads `requires-python`, downloads it on first `uv run`); install llama.cpp (macOS `brew install llama.cpp`, `llama-server --version`; Linux/Windows use llama.cpp releases, same commands); the toolchain the later lesson grades with (`uvx ruff --version`, `uvx pyrefly --version`, noting `uvx` caches them so grading is not a later tangent); start the server (`uv run scripts/backend.py start`, then `status`); chat once (`chat "hello"`, note the Q4_K_M download on first start and the 8.38 GB peak); stop it (`stop`); connect Pi (`PI_CODING_AGENT_DIR=$PWD/learn/code/profile pi -p --provider llamacpp --model Mellum2.1-12B-A2.5B-Thinking --no-approve --no-extensions --no-skills --no-prompt-templates --no-themes --no-context-files --no-session "Say hello in one line"`); "What you have" and next-lesson pointer. Add the nav entry, and rewrite the index's lesson 1 entry to link the page instead of saying "coming".
- [ ] **Step 4: Run it and see it pass.** `node --test tests/learn-site.test.mjs` → PASS. Add the changelog `Added` entry: "Getting started lesson 1 walks a machine with no Python from `uv` to a first base-Pi answer on llama.cpp, with the model settings in `pyproject.toml` and a private profile that leaves `~/.pi` alone."
- [ ] **Step 5: Commit.** `git add learn/getting-started zensical.toml tests/learn-site.test.mjs CHANGELOG.md && git commit -m "docs(lc2): lesson 1, base Pi on llama.cpp"`

---

### Task 6: Maintainer pages

**Files:**
- Create: `learn/project/index.md`, `learn/project/toolchain.md`
- Modify: `zensical.toml`, `tests/learn-site.test.mjs`, `CHANGELOG.md`

**Interfaces:**
- Produces: a `Project` nav group after `About`, holding `project/index.md` and `project/toolchain.md`; no `track` front matter (they are not lessons).

- [ ] **Step 1: Write the failing test.** Add both pages to `PAGES` and the nav check. One test asserts `learn/project/index.md` mentions `scripts/backend.py`, `docs/sdd.md` and `AGENTS.md`; `learn/project/toolchain.md` mentions `pyproject.toml`, `[tool.mellum]`, `uv run scripts/backend.py`, `PI_CODING_AGENT_DIR`, `npm test`, `uv run pytest` and `uvx zensical build`.
- [ ] **Step 2: Run it and see it fail.** `node --test tests/learn-site.test.mjs` → FAIL, pages missing.
- [ ] **Step 3: Write the two pages.** `index.md`: what the repo is (worker package plus ladder plus Learning Center), a table of the top-level directories, where records live (`evals/`, `docs/superpowers/`), and links to `README.md`, `AGENTS.md`, `docs/sdd.md` through GitHub URLs. `toolchain.md`: clone and `uv`; the root `pyproject.toml`; the `backend.py` commands; the generated profile and `PI_CODING_AGENT_DIR`; checks (`npm test`, `uv run pytest` under `ladder/`, `node build.mjs`, `uvx zensical build`); release (tag, changelog, README pins). Add the nav group.
- [ ] **Step 4: Run it and see it pass.** `node --test tests/learn-site.test.mjs` → PASS. Changelog `Added`: "A Project section in `learn/` for maintainers: what the repo contains, the `uv` and `pyproject.toml` toolchain, the backend commands, the checks and the release steps."
- [ ] **Step 5: Commit.** `git add learn/project zensical.toml tests/learn-site.test.mjs CHANGELOG.md && git commit -m "docs(lc2): maintainer pages for how the project works"`

---

### Task 7: Retire the Justfile and rewrite the backend doc

**Files:**
- Delete: `Justfile`
- Modify: `docs/backends/llamacpp.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: everything above. No new test: `tests/docs.test.mjs` already fails on a broken relative link, and `docs-caps` guards size.

- [ ] **Step 1: Rewrite `docs/backends/llamacpp.md`** around the script: replace the install/weights/serve sections' `just` commands with `uv run scripts/backend.py start|status|chat|stop`, keep the quant table, the flags in `serve_argv`, the settings table (pointing at `[tool.mellum]`), the measured table (8.38 GB peak, 207 tok/s, 72.2 tok/s prompt eval), "Why 50k context is cheap here", and Open. Add: "2026-10-20: the Justfile that shipped in `b51a1e8` was retired before release for `scripts/backend.py`, because the learner already installs `uv` and the same file can hold the settings."
- [ ] **Step 2: Delete the Justfile** with `git rm Justfile`.
- [ ] **Step 3: Reconcile `CHANGELOG.md`.** Replace the Justfile `Added` bullet with: "`uv run scripts/backend.py serve|start|status|stop|chat` runs Mellum 2.1 through llama.cpp, reading `[tool.mellum]` in the root `pyproject.toml`; the Justfile it replaces never reached a release." Keep the llamacpp doc bullet, now describing the script.
- [ ] **Step 4: Run the gates.** `npm test` → 322+ pass, no broken links; `node --test tests/docs-caps.test.mjs` → 4/4; `uv run scripts/backend.py --help` and `uv run scripts/backend.py profile --dry-run` print what the doc says.
- [ ] **Step 5: Commit.** `git add docs/backends/llamacpp.md CHANGELOG.md && git commit -m "chore(lc2): retire the Justfile for the backend CLI"`

---

## Verification

- `npm test` and `node --test tests/docs-caps.test.mjs` pass on the branch.
- `uv run scripts/backend.py profile --dry-run` equals `learn/code/profile/models.json`.
- The live smoke (download Q4_K_M, start, chat, Pi answer) is the lesson's own check; it needs the weights and is not part of the suite.

## Result

2026-10-20. Shipped on `learning-center`, unreleased: the root
`pyproject.toml` (`requires-python = ">=3.14"`, `[tool.mellum]`),
`scripts/backend.py` with `serve`, `start`, `stop`, `status`, `chat` and
`profile` replacing the Justfile, the generated
`learn/code/profile/models.json`, Getting started lesson 1, and the
maintainer pages in `learn/project/`.

Verified: `npm test` 334/334, `tests/docs-caps.test.mjs` 4/4,
`uvx zensical build` clean, and a live smoke on the M5 Max — `start`
served `Q4_K_M` with `n_ctx` 50176, `chat` answered in 94 tokens, and base
Pi through the private profile replied "Hello". The 8.38 GB peak was not
re-measured in this run.
