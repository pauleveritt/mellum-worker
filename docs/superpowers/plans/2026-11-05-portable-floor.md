---
phase: LC
feature_cycle: LC.39
cycle: 1
lifecycle: active
---

# Portable rig and the Vanilla floor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a native Vanilla session count on any qualified machine by pinning the software, qualifying each host and limiting sessions by requests and tokens. Then collect the preregistered floor on two CUDA rentals and the Mac.

**Architecture:** The controller runs on the inference host, with no Docker. Each host checks out the repo at the cohort's commit and bootstraps pinned tools from the pin card. It serves llama-server as root and runs each session natively as an unprivileged user behind a local budget proxy. Each session is followed by a sweep. A conformance check writes a host card per rental, and a cohort driver applies the preregistered validity, replacement and portability rules.

**Tech Stack:** Python 3.14 through `uv run` (`learn/code`), Node 24 (`scripts/containment/relay.mjs` in its new proxy mode), llama.cpp b11669 (Metal and CUDA), OpenSSH with `tmux` on the pod, and the Runpod MCP for rentals.

**Spec:** [`docs/superpowers/specs/2026-11-05-portable-floor-design.md`](../specs/2026-11-05-portable-floor-design.md), with the [preregistration](../research/2026-11-05-portable-floor-preregistration.md). Executors read both.

## Global Constraints

- Weights: HF revision `4159d684ffdb09ba89dc2a58feb3e75c54eef036`, file `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf`, SHA-256 `ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755`.
- Build: llama.cpp b11669, commit `620d2225c`; the server's `build_info` is `b11669-620d2225c`. CUDA builds use `GGML_NATIVE=OFF`.
- Server: `-c 100000 -np 2 --no-kv-unified --jinja -fa on --cont-batching -b 512 -ub 512 -ctk q8_0 -ctv q8_0 -ngl 999 -lv 4`, 50,176 tokens per slot. Threads are recorded, not pinned.
- Client: temperature 1.0, top-p 0.95, top-k 20, `max_tokens` 16,384.
- Bootstrap pins:
  - Node 24.22.1, checked by per-platform SHA-256;
  - uv 0.11.6 and Python 3.14.2;
  - `@earendil-works/pi-coding-agent@1.4.0`;
  - the frozen dependency project: the Easy suite's `learn/code/suites/easy/base/pyproject.toml` and `uv.lock`, synced with `--frozen`, as the image build did;
  - ruff 0.16.3, complexipy 8.3.0, pyrefly 1.2.0, and pytest at the suite's pin;
  - `procps`, `lsof` and `git`.
- Acceptance package `af4122164322e6446b5cb12728693ca32749fdaec2606aa35e1bcaf9e41e3dd9`, observe-only, with `checker.py` and the manifest unchanged.
- Session budget: 120 requests, 64,000 output tokens, a 180 s open tool call and a 3,600 s wall safety net. A request with no usage is charged 16,384.
- One session at a time per host. Session user `mellum-session`, grading user `mellum-grade`. Mac records are flagged `uncontained`.
- **No Docker anywhere.** The rig code never rents, stops or terminates. **Every rental needs the user's yes in chat**, stating the GPU model, provider, region, price per hour, expected hours and the host it serves.
- Test-first, every test shown failing first. Use `uv run`, never a bare `python`. Stage explicit paths. Never commit `trace.jsonl`, `stdout.txt` or `diff.patch`. No remedy, worker or gate in the floor arm, and no suite path, route or value in rig code.

## Review Focus

1. **A budget reached mid-stream.** The in-flight response is forwarded whole, the next request is refused, and the session ends `budget`. This is owned by Task 4.
2. **Usage that never arrives**, after a reset or a truncated stream. It is charged 16,384 and recorded as unknown, never zero. This is owned by Task 4.
3. **A session that calls llama-server directly.** The server logs a generation the proxy never created, and the session is invalid. This is owned by Task 9.
4. **A host card that predates the current pin card.** The driver refuses to count on it. This is owned by Task 9.
5. **A session process that escapes the group and workspace sweeps**, for example a `setsid` server started from `/tmp`. The user sweep must kill it by uid, and if a listener remains, the host stops. This is owned by Task 6.

---

### Task 1: Pin card and server command

**Files:**
- Create: `scripts/rig/pins.json` and `learn/code/rig.py`
- Modify: `scripts/baseline/pins.env`, adding one pointer comment only
- Test: `learn/code/tests/test_rig.py`

**Interfaces:**
- Produces:
  - `PINS: Path` and `load_pins(path: Path = PINS) -> dict`, which raises `ValueError` naming the first missing or wrong key;
  - `pins_digest(pins: dict) -> str`, the SHA-256 of canonical JSON;
  - `server_argv(pins, *, binary: str, model: str, port: int, threads: int, log: str) -> list[str]`.
- `pins.json` keys:
  - `weights`;
  - `build` (tag, commit, build_info, cuda_architectures);
  - `server` (the flags as data);
  - `client` (sampling, max_tokens);
  - `bootstrap` (node version and sha256 per platform, uv, python, pi, checkers, apt packages);
  - `acceptance_package_sha256`;
  - `session` (`max_requests`, `max_output_tokens`, `max_tokens_per_request`, `unknown_usage_charge`, `open_tool_seconds`, `wall_safety_seconds`);
  - `allowlist` (`min_compute_capability` "8.0", `gpu_count` 1, `min_driver_major`, `platform` "linux-x86_64").

- [ ] **Step 1: Write the failing tests.**
  - `test_pins_carry_frozen_identity` asserts the weights sha256, the `build_info`, the session values and the bootstrap versions from Global Constraints.
  - `test_load_pins_refuses_auto_flash_attention` loads a copy with `"flash_attention": "auto"` and expects `ValueError`.
  - `test_server_argv_matches_frozen_set` is:

```python
argv = rig.server_argv(rig.load_pins(), binary="llama-server", model="/m.gguf", port=18001, threads=16, log="/l")
assert argv[argv.index("-fa") + 1] == "on" and argv[argv.index("-np") + 1] == "2"
assert argv[argv.index("-c") + 1] == "100000" and "--no-kv-unified" in argv and argv[-2:] != ["-fa", "auto"]
```

- [ ] **Step 2:** Run `uv run python -m pytest learn/code/tests/test_rig.py -v`. Expected: FAIL, because `rig` cannot be imported.
- [ ] **Step 3:** Write `pins.json` and implement `rig.py`. The argv order follows `evals/2026-11-05-log-follow-screen/backend-config.json`, and the bootstrap versions follow `scripts/containment/Dockerfile`. Add the pointer comment to `pins.env` and change none of its values.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: add the portable rig pin card and server command`.

### Task 2: Host commands — checkout, bootstrap, build, fetch, serve

**Files:**
- Modify: `learn/code/rig.py`
- Test: `learn/code/tests/test_rig.py`

**Interfaces:**
- Produces, each returning the shell command strings for a fresh Linux pod, built only from `pins.json` so that nothing can drift:
  - `checkout_commands(repo_url: str, commit: str, dest: str) -> list[str]`;
  - `bootstrap_commands(pins, *, prefix: str) -> list[str]`;
  - `build_commands(pins, *, prefix: str) -> list[str]`;
  - `fetch_weights_commands(pins, *, dest: str) -> list[str]`;
  - `serve_commands(pins, *, binary, model, port, threads, log) -> list[str]`;
  - `stop_server_commands() -> list[str]`;
  - `user_commands() -> list[str]`, which creates `mellum-session` and `mellum-grade` without a password or sudo.
- Produces: `tool_versions(prefix: str) -> dict[str, str]`, which reads back each installed bootstrap version on the current machine.

- [ ] **Step 1: Write the failing tests.**
  - `test_bootstrap_checks_node_hash` checks that a `sha256sum --check` precedes the Node extraction.
  - `test_bootstrap_installs_exact_versions` checks for `pi-coding-agent@1.4.0`, `python install 3.14.2` and `uv sync --frozen`.
  - `test_build_commands_pin_commit_and_native_off` checks for `620d2225c`, `-DGGML_NATIVE=OFF` and the pinned arch list.
  - `test_fetch_weights_checks_hash` checks that the last command verifies the pinned sha256.
  - `test_serve_commands_use_server_argv` checks that the joined command contains `shlex.join(server_argv(...))`.
  - `test_checkout_is_exact_commit` checks for `git checkout --detach <commit>` followed by a `rev-parse` check.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement them. The server runs in a detached `tmux` session named `mellum-rig`.
- [ ] **Step 4:** Run them. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: generate pinned checkout, bootstrap, build and serve commands`.

### Task 3: Relay proxy mode

**Files:**
- Modify: `scripts/containment/relay.mjs`
- Test: `tests/containment-relay.test.mjs`

**Interfaces:**
- Produces: `rewriteRequest(body: Buffer) -> Buffer`. It sets `stream_options.include_usage = true` when `stream` is true, preserves every other field, and throws on JSON that is not an object.
- Produces: `proxyRelay({listen: number, target: string, log, budget: null|{...}}) -> Promise<{port, close()}>`, a loopback HTTP proxy that reuses `allowedRoute` and `hostRelay`'s logging boundaries (`created`, `headers`, `complete`, `stream_error`, `request_error`), plus `rewritten`.
- The CLI gains `node relay.mjs proxy --listen PORT --target URL --log FILE`. The `host` and `container` modes stay unchanged.

- [ ] **Step 1: Write the failing tests.**
  - `rewriteRequest adds only include_usage`: a body with `messages`, `max_tokens` and `stream: true` comes back equal apart from `stream_options`.
  - `rewriteRequest refuses non-object JSON`: a body of `[]` throws.
  - `proxy forwards response bytes unchanged`: a local `createServer` streams fixed bytes, and the bytes a client receives through the proxy are identical.
  - `proxy refuses non-inference routes`: `POST /slots/0?action=save` gets 403 and the server sees nothing.
- [ ] **Step 2:** Run `node --test tests/containment-relay.test.mjs`. Expected: FAIL.
- [ ] **Step 3:** Implement it. The proxy buffers a chat-completion body up to `MAX_BODY`, rewrites it, then forwards it. GET routes pass through untouched.
- [ ] **Step 4:** Run the relay tests. Expected: PASS, including every existing relay test.
- [ ] **Step 5:** Commit with `feat: add a loopback proxy mode to the inference relay`.

### Task 4: Proxy enforces the session budget

**Files:**
- Modify: `scripts/containment/relay.mjs`
- Test: `tests/containment-relay.test.mjs`

**Interfaces:**
- Produces: `usageFrom(bytes: Buffer, contentType: string) -> number|null`, which returns the last `usage.completion_tokens` in SSE `data:` lines or in a JSON body.
- Produces: `budget = {requests, outputTokens, unknownCharge}`, with CLI flags `--max-requests`, `--max-output` and `--unknown-charge`.
- Log rows: `usage` with `{id, outputTokens: number|null, charged}`, and `budget_exhausted` with `{requests, outputTokens}`, written once.

- [ ] **Step 1: Write the failing tests.**
  - `usageFrom reads the final SSE usage chunk`: the third chunk carries 42, and the result is 42.
  - `budget refuses after the limit, never in flight`: with a budget of 2 requests, requests 1 and 2 complete and request 3 gets a 429 with body `{"error":"session budget exhausted"}`. The server is hit twice.

```js
assert.equal(serverHits, 2);
assert.equal(rows.filter(r => r.boundary === 'budget_exhausted').length, 1);
```

  - `budget charges unknown usage`: the server resets mid-stream, and the log has a `usage` row with `outputTokens: null, charged: 16384`.
  - `budget counts output across requests`: with an output limit of 100 and two 60-token replies, the third request is refused.
- [ ] **Step 2:** Run the relay tests. Expected: FAIL.
- [ ] **Step 3:** Implement it. The check runs before any upstream request. Output is charged at `complete`, and the unknown charge is applied at `stream_error` and `request_error`.
- [ ] **Step 4:** Run the relay tests. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: enforce per-session request and output budgets at the proxy`.

### Task 5: Native session runs as a user and ends on budget

**Files:**
- Modify: `learn/code/harness.py`. That covers `run_suite` (434–596), `wait_or_stall` (597–634) and `execution_outcome` (901–932).
- Test: `learn/code/tests/test_harness.py`

**Interfaces:**
- Produces: `run_suite(..., user: str | None = None, budget_log: Path | None = None, wall_safety: float | None = None)`.
  - With `user`, Pi starts through `Popen(user=user)` and the run directory is chowned to that user.
  - With `budget_log`, the wait loop ends the session when that file gains a `budget_exhausted` row.
  - `wall_safety` replaces `deadline` as the watchdog.
- Produces: `termination_reason` values `"budget"` and `"wall_safety"`, which pass through `execution_outcome(run)["completion"]`.

- [ ] **Step 1: Write the failing tests.**
  - `test_wait_ends_on_budget_row`: a fake child sleeps 30 s, a row is appended after 0.3 s, and the result is `"budget"` within 2 s.
  - `test_wall_safety_classified`: `wall_safety=0.5` gives `"wall_safety"`.
  - `test_execution_outcome_reports_budget_and_wall_safety`: both values pass through.
  - `test_without_budget_behaviour_unchanged`: the existing deadline path still returns `"deadline"`.
- [ ] **Step 2:** Run `uv run python -m pytest learn/code/tests/test_harness.py -k "budget or wall_safety or unchanged" -v`. Expected: FAIL.
- [ ] **Step 3:** Implement it. When none of the new arguments is given, behaviour is byte-for-byte as today.
- [ ] **Step 4:** Run the whole `learn/code/tests` suite. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: run native sessions as a given user and end them on budget`.

### Task 6: User isolation and sweep

**Files:**
- Create: `learn/code/isolation.py`
- Test: `learn/code/tests/test_isolation.py`

**Interfaces:**
- Produces:
  - `listeners(uid: int | None = None) -> list[dict]`, which parses `lsof -nP -iTCP -sTCP:LISTEN`;
  - `user_processes(uid: int) -> list[tuple[int, str]]`;
  - `sweep_user(name: str, *, grace: float = 1.0) -> dict`, which kills by uid after the existing group and workspace sweeps, then deletes and recreates the home. It returns `{killed, listeners_after, home_reset, ok}`;
  - `preflight_mac(ports: list[int] | None = None) -> dict`, which returns `{ok, listeners}`;
  - `isolation_probe(session_user: str, protected: list[Path], pids: list[int]) -> dict`, which returns `{ok, findings}`.

- [ ] **Step 1: Write the failing tests.** They run as the current user, so the uid sweep is exercised on a throwaway child.
  - `test_sweep_kills_setsid_listener`: start `python -c` with a socket listening on an ephemeral port under `setsid`, sweep by the current uid restricted to that child's process tree, and assert that the listener is gone and `ok` is true.
  - `test_sweep_reports_failure_when_listener_survives`: monkeypatch the kill to no-op and expect `ok: false`.
  - `test_listeners_parse`: a fixed `lsof` sample gives the expected port and pid.
  - `test_isolation_probe_flags_readable_secret`: a file with mode 0644 in the protected list is reported.
- [ ] **Step 2:** Run `uv run python -m pytest learn/code/tests/test_isolation.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement it with the standard library, `lsof` and `kill`. Never raise from `sweep_user`, matching the existing sweeps.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: sweep and probe native session-user isolation`.

### Task 7: Native acceptance probe

**Files:**
- Create: `learn/code/acceptance_native.py`
- Test: `learn/code/tests/test_acceptance_native.py`

**Interfaces:**
- Consumes: `AcceptancePackage`, `isolation.sweep_user`, and `scripts/containment/probe.py` and `pytest_probe.py` unchanged.
- Produces: `NativeProbe(snapshot: Path, control: Path, *, deadline_at: float, user: str | None, python: Path)`.
  - It has the same `run(name, inputs, timeout) -> dict` contract and the same fixed names `home`, `titles`, `startup` and `tests` as `CandidateProbe`.
  - It copies the snapshot to a fresh directory owned by `user`.
  - It runs `python -I probe.py NAME` there with the frozen dependency venv's interpreter.
  - It caps output at 1 MiB and sweeps the user on exit.
- Produces: `check_snapshot_native(snapshot, package, control, timeout, *, user, python) -> dict`, which mirrors `check_snapshot`'s statuses `integrity_error`, `timeout` and `checker_error` and its result file.

- [ ] **Step 1: Write the failing tests.** They use the known-good and known-broken Phase 1 fixtures that `acceptance_qualification.py` already uses.
  - `test_native_known_good_passes`.
  - `test_native_known_broken_fails`.
  - `test_native_probe_rejects_unknown_name`.
  - `test_native_probe_times_out`, using a fixture whose startup never binds, which gives `probe_error` within the timeout.
  - `test_package_hash_unchanged`, which checks that `AcceptancePackage.load(...).digest` equals the pinned `af41…dd9`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement it. On the Mac, `user=None` runs as the operator and the result is flagged `uncontained`.
- [ ] **Step 4:** Run them. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: run the acceptance probe natively as a grading user`.

### Task 8: Conformance check and host card

**Files:**
- Create: `learn/code/conformance.py` and `scripts/rig/ppl.txt`, a fixed text written for this
- Test: `learn/code/tests/test_conformance.py`

**Interfaces:**
- Consumes: `rig.load_pins`, `rig.pins_digest`, `rig.tool_versions`, `isolation.isolation_probe`.
- Produces:
  - `parse_perplexity(text: str) -> float`;
  - `identity_problems(props: dict, slots: list[dict], pins: dict) -> list[str]`;
  - `check(pins, endpoint: str, *, perplexity_binary: Path, model: Path, reference_ppl: float | None, tolerance: float, host: dict, out: Path) -> dict`.
- `host-card.json` has these fields:
  - `passed` and `pins_digest`;
  - `items`, one each for identity, capacity, protocol, numerics, throughput, stability, tooling and isolation, each `{passed, detail}`;
  - `gpu`, with name, vram_mib, driver, cuda and compute_capability, or `"metal"`;
  - `provider`, `region`, `rental_id`, `price_per_hour`, `threads` and `checked_at`;
  - `post_check`, which starts null;
  - `stopped`, which starts null.

- [ ] **Step 1: Write the failing tests.**
  - `test_parse_perplexity`: `Final estimate: PPL = 7.1234 +/- 0.05123` gives 7.1234.
  - `test_identity_problems`: matching inputs give none, and a wrong `build_info`, an `n_ctx` other than 50,176 and a single slot each give one problem.
  - `test_check_against_fake_server`: a stdlib `ThreadingHTTPServer` serves `/props`, `/slots`, `/health` and a streaming completion that honours `max_tokens`. A stub perplexity binary prints a fixed line. The result is `passed: true` with every item present.
  - `test_check_fails_when_max_tokens_clamped`: the fake caps at 8,192, and `protocol.passed` is false.
  - `test_numerics_out_of_tolerance_fails`.
- [ ] **Step 2:** Run `uv run python -m pytest learn/code/tests/test_conformance.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement it with the standard library only.
  - The protocol item sends one tool-call request and one reasoning request.
  - The stability item sends ten back-to-back short requests.
  - The capacity item sends one full-context request per slot, in turn.
  - Numerics runs `llama-perplexity -c 2048` over `ppl.txt`. With `reference_ppl=None`, it records `reference` instead of passing or failing.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: add per-rental conformance check and host card`.

### Task 9: Floor policy

**Files:**
- Create: `learn/code/floor.py`
- Test: `learn/code/tests/test_floor.py`

**Interfaces:**
- Consumes: `rig.pins_digest`, a host card, `acceptance_budget.reconcile` and `wilson`.
- Produces:
  - `PLAN = {"A": 6, "B": 6, "M": 3}` and `MAX_REPLACEMENTS = 2`.
  - `card_usable(card, pins) -> tuple[bool, str]`, which is false when the card failed or its `pins_digest` is stale.
  - `validity(execution: dict, budget: dict, sweep: dict, recovered: bool, post_check: str) -> tuple[str, str]`, which returns `"counted"` or `"invalid"` and a reason.
    - Invalid when the session hit `wall_safety`, when `budget["reconciled"]` is false (the server logged generations the proxy did not create), when there is an unrecovered transport error, when the sweep failed or the Mac preflight found a listener, or when `post_check == "failed"`.
    - `post_check == "unavailable"` stays counted and is flagged.
  - `may_replace(host_state) -> bool`.
  - `session_record(run: Path, card: dict) -> dict`. It returns the completion; the hidden checks and `checks_ran`; health; layout; each acceptance check by name; `usable` by the LC.34 rule; the reconciled budget; `rental_id`; and `uncontained`.
  - `portability(a: list[dict], b: list[dict]) -> dict`, which returns `{"portable": bool, "reasons": [...]}`.
  - `summarize_floor(records) -> dict`, which reports per host, pooled A+B and pooled A+B+M, with Wilson intervals.

- [ ] **Step 1: Write the failing tests.**
  - `test_stale_card_refused`.
  - `test_proxy_bypass_is_invalid`, built from a reconcile result with an extra server generation.
  - `test_failed_sweep_is_invalid`.
  - `test_lost_rental_sessions_count_flagged`.
  - `test_replacement_cap`.
  - `test_usable_follows_lc34_rule`, where everything passes except `title_override` and the record is unusable.
  - `test_portability_rule`:

```python
assert not floor.portability(rows(hidden=0), rows(hidden=4))["portable"]   # 0/6 vs 4/6
assert floor.portability(rows(hidden=1), rows(hidden=4))["portable"]       # gap of 3
assert not floor.portability(rows(budget=3), rows(budget=0))["portable"]
```

- [ ] **Step 2:** Run `uv run python -m pytest learn/code/tests/test_floor.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement it. The functions are pure apart from reading the run directory.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit with `feat: encode the floor's validity, replacement and portability rules`.

### Task 10: Floor cohort driver

**Files:**
- Create: `scripts/floor_cohort.py`
- Test: `learn/code/tests/test_floor_cohort.py`
- Modify: `CHANGELOG.md`, under `[Unreleased]` → Added

**Interfaces:**
- Consumes: Tasks 1–9, `harness.run_suite`, `harness.score_details`, and `acceptance_overnight.freeze_files` and `verify_files`.
- Commands run on the host itself, one shell line each:
  - `prepare BATCH` verifies `tool_versions` against the pins and freezes the inputs, pins and package.
  - `host BATCH NAME --provider P --region R --rental-id ID --price-per-hour X` runs conformance and writes `hosts/NAME/<rental-id>/host-card.json`. On the Mac the flags are `--provider local`.
  - `run BATCH NAME` collects counted sessions up to `PLAN[NAME]`. Per session it does the following:
    1. starts the proxy with the budget;
    2. runs `run_suite` as `mellum-session`, or as the operator on the Mac after `preflight_mac`;
    3. reconciles the server log window for that session;
    4. runs the observe-only acceptance and hidden grading as `mellum-grade`;
    5. sweeps both users and writes the record.

    It replaces only invalid sessions, up to the cap, and resumes from `batch.jsonl`.
  - `post-check BATCH NAME` re-runs identity, stability and tooling.
  - `report BATCH` writes `records.json`, `summary.json`, `portability.json` and `scorecard.md`, giving per-host tables first.
- `record-stop BATCH NAME RENTAL --state S --storage-billing yes|no` runs on the Mac after the batch is copied back. It records the stop state that the operator read through the Runpod MCP.

- [ ] **Step 1: Write the failing tests.** They use fakes, with no model. Stub `run_suite` to write a run directory and stub the proxy log. Assert that:
  - `run` refuses a host with no usable card;
  - it never starts a session while another is running on the same host;
  - it replaces only invalid sessions, at most twice;
  - a resumed `run` does not recount;
  - `report` puts per-host tables before pooled ones.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement the driver. It never calls a provider API.
- [ ] **Step 4:** Run the whole `learn/code/tests` suite and `npm test`. Expected: PASS.
- [ ] **Step 5:** Add the `[Unreleased]` entry. It covers the portable floor driver, native sessions with no Docker, request and token budgets in place of the wall-clock deadline for its cohorts, and per-rental host cards.
- [ ] **Step 6:** Commit with `feat: add the portable floor cohort driver`.

### Task 11: Qualify the rig on the Mac

**Files:**
- Create: `evals/<date>-portable-floor/qualification/`, retained JSON only

- [ ] **Step 1:** Run `prepare` on a fresh batch under `runs/`. Expected: tool versions match and the freeze is written.
- [ ] **Step 2:** Run the fake-provider cases through the real native path, and retain each record:
  - a session reaching the request budget ends `budget`;
  - a stream reset charges 16,384;
  - a direct call to the fake server's port, bypassing the proxy, makes the session invalid;
  - a `setsid` listener left by the session is swept.
- [ ] **Step 3:** Run `host BATCH M --provider local` against the real Mac llama-server started with `rig.server_argv`. Its perplexity becomes the reference. Expected: `passed: true`, with `isolation` recorded as `uncontained`.
- [ ] **Step 4:** Commit the retained records with `docs: qualify the portable rig natively on the Mac`.

### Task 12: Collect the floor

Each rental stops for the user's yes in chat. The driver runs in `tmux` on its host. The operator shows it in a visible Terminal tab over SSH, with the watcher following the newest trace.

- [ ] **Step 1:** Run `run BATCH M` on the Mac. Expected: three counted sessions, or invalid ones replaced within the cap.
- [ ] **Step 2:** **Rental A.** Read Runpod capacity through the MCP and propose one allowlisted Ampere or Ada GPU with its price, region and expected hours. **Wait for yes.** Create the pod. Over SSH, run Task 2's commands in this order: users, checkout, `lock_checkout_commands`, bootstrap, build, fetch, serve. Put the batch outside `/root` (for example `/srv/mellum/<batch>`), since the session user must traverse it. *(Dated 2026-11-05, after the final review: the order and the lock close the hidden-oracle and ownership findings.)*
- [ ] **Step 3:** Run `prepare`, then `host BATCH A`, calibrating the numerics tolerance against the Mac reference, then `run BATCH A` and `post-check BATCH A`.
- [ ] **Step 4:** Copy the batch back. Stop the pod through the MCP, read back its state, and run `record-stop`. Report any billed storage to the user.
- [ ] **Step 5:** **Rental B.** Repeat for one Hopper or Blackwell GPU, with the same stop for yes and the same steps.
- [ ] **Step 6:** If a rental is lost, propose its replacement as a new rental and wait for yes, per the preregistration.

### Task 13: Report and close

**Files:**
- Create: `evals/<date>-portable-floor/`, holding `README.md`, `scorecard.md`, `records.json`, `summary.json`, `portability.json` and `host-cards/`
- Create: `docs/superpowers/research/<date>-portable-floor.md`
- Modify: `ROADMAP.md`, for LC.39's Status and `## Now`
- Modify: `learn/glossary.md`
- Modify: `learn/pathologies.md`, only if a new failure shape appeared
- Modify: `BACKLOG.md`, the compaction-accounting entry, if its reopen condition is met

- [ ] **Step 1:** Run `report BATCH` and copy the outputs into `evals/` with the raw files stripped.
- [ ] **Step 2:** Write the research note. It opens with the per-host table, then the pooled table, then the portability reading, quoting the preregistered rule verbatim. A usable count near zero is reported as anticipated, not as a finding.
- [ ] **Step 3:** Add glossary entries for **pin card**, **host card**, **conformance check**, **session budget** and **session sweep**.
- [ ] **Step 4:** Update LC.39's Status and `## Now`. Write this plan's `## Result`, set `lifecycle: closed` and move it to `plans/archive/`.
- [ ] **Step 5:** Run `node --test tests/docs-caps.test.mjs`, `npm test` and `uv run python -m pytest learn/code/tests`. Reconcile `[Unreleased]` with `git log v0.1.8..HEAD --oneline`.
- [ ] **Step 6:** Commit with `docs: record the Vanilla floor on the portable rig`. Ask before publishing any raw evidence release.

## Result

(written at close)
