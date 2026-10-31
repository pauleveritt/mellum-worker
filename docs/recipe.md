# Mellum Worker and Mellum Worker: Mellum 2.1 as a coding worker under Pi

**Status: shipped 2026-10-09; two ways to use the worker (§4 delegated, §4b in-session), both measured. 2026-10-20: the delegated Worker and the OpenCode port were retired; §4 is history, and §4b is the shipped shape. What remains is in [`ROADMAP.md`](../ROADMAP.md) (M.11, M.12) and [`BACKLOG.md`](../BACKLOG.md); the [2026-10-09 table](superpowers/research/2026-10-09-future-work.md) is history. Every number links to its record under `evals/`; the lean-down that produced the shipped worker is summarised in [ablation-summary.md](ladder/ablation-summary.md).**

Installed from this repo; measured by the ladder (`ladder/`), whose fixtures and phase records (`evals/`) live here too.

This is the practical recipe that came out of the research in
[docs/superpowers/research/](superpowers/research/) and [evals/](ladder/): run the local Mellum 2.1 model not as the agent
you talk to, but as a narrowly configured *child* that your normal Pi session
hands bounded coding tasks to. Everything here was measured with the prompt
ladder (`ladder/`); the numbers link to their records.

## 1. What this is, and is not

Mellum 2.1 Thinking (12B MoE, 2.5B active, Q6 MLX conversion) could not run
the Superpowers workflow as the primary agent: it dispatched skill names as
agents, retried after errors, and ended turns without answering
([recovery report](superpowers/research/2026-10-07-mellum-recovery/report.md)). The same
model, given a clean prompt and file tools only, completes bounded tasks.

So the recipe inverts the roles. Your usual model (DeepSeek Flash here) stays
the parent with Superpowers and pi-subagents; Mellum is `mellum-worker`, a
child with `read, grep, find, ls, bash, edit, write`, no skills catalog, no
bootstrap, no delegation, and a prompt made of facts about the test
command.

What it is good for, measured: one-line fixes, adding a function with its
test, a rename across two files, and three-file changes with a named failing
test. What it is not: exploration, design, or scoping a task from a symptom
on its own (see the ladder results below).

## 2. Inference server (oMLX)

Serve it as described in [backends/omlx.md](backends/omlx.md). The converted model is published at
<https://huggingface.co/pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit>
(9.9 GB, two safetensors shards, MLX 6-bit), so it can be pulled with
`hf download pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit` instead of
converted. Settings: 56,000-token context window, native hybrid cache,
cache quantization off, one concurrent request.

**Which settings actually apply.** oMLX gives a request's sampling and cap
values precedence over the per-model profile, except that `force_sampling`
makes the server's temperature, top_p and top_k win and `forced_ct_kwargs`
makes the server's listed chat-template keys win. Pi sends `max_tokens`,
`temperature`, `top_p`, `top_k`, `min_p`, `presence_penalty` and
`repetition_penalty` on every request from its `models.json` entry, and
with `thinkingFormat: qwen-chat-template` it sends `chat_template_kwargs`
with `enable_thinking` and `preserve_thinking` true. The archived traces of the Mode and Worker
phases (A10, A17 and A19, so also A14 and A18–A20) show every Mellum request
carrying `max_tokens` 16,384, thinking on and sampling 1 / 0.95 / 20, so the
`baseline` server profile's `max_tokens` 4,096 was overridden; only the
direct-mode research phases (A3 and earlier), where the ladder sends its own
request values, ran at 4,096. So:

| setting | where it is decided | value used |
| --- | --- | --- |
| `max_tokens` | Pi `models.json` → `maxTokens`, which wins over the server profile | 16,384 (model-card per-turn budget) in every Mode and Worker request; in direct mode a 4,096 cap cut off one three-file run mid-thought ([phases 1c/1d](ladder/phase1d-tuned-effective/README.md)) |
| temperature / top_p / top_k | Pi `models.json` → `samplingParams`, else Pi defaults | Pi default is 1 / 0.95 / 20 (the model card's agentic sampling) |
| presence / repetition penalty | request | 0 / 1.0 — 0.5 showed nothing measurable (1c vs 1d: 13/15 vs 14/15, same request and error counts), though that comparison changed the cap at the same time |
| thinking budget | server profile only | off — a 4,096-per-block budget was never triggered in 15 runs; the request cap is what binds. On a server with `reasoning_parser` set (such as `qwen_3`) a server thinking budget may take effect, unlike in A13 (oMLX builds the budget processor when its output parser knows the think-close token), so `/mellum check` fails when it is on |
| `max_tool_result_tokens` | server profile only | off — the largest tool result in 30 runs was 2,639 characters; `/mellum check` fails when a cap is set |
| thinking on/off | request: `chat_template_kwargs` from `thinkingFormat`; a server `forced_ct_kwargs` would override it | on in every Mode and Worker request; the ladder's server profile left `forced_ct_kwargs` unset, and setup step 3 forces it on for clients that send nothing |
| thinking level (`thinking:` in the agent file, `--thinking`) | nowhere | inert: Pi's level does not reach an `openai-completions` provider; two runs at "high" and "medium" sent byte-identical requests ([ablation A5](ladder/ablation-a5-thinking-medium/README.md)) |
| `thinking_budget` (request field) | a hook can send it (A13's hook, removed from the ladder on 2026-10-13 as inert) | not enforced for this model: oMLX needs a reasoning parser configured to build its budget processor ([A13](ladder/ablation-a13-budget-medium/README.md)) |

Verify with one request through the proxy or Pi's `before_provider_request`
hook (`ladder/ladder/record-pi.js`) that the values you expect are the values sent;
the ladder records them per run as `effective_params`.

## 3. Pi setup

All of this is written by the setup skill into your user-scope Pi directory: the agent file at `~/.pi/agent/agents/`, the `models.json` entry, and the extensions come with the package.

- `~/.pi/agent/agents/mellum-worker.md` (written by the setup skill from `templates/pi/mellum-worker.agent.md`) — the worker. Each frontmatter line removes
  something: `systemPromptMode: replace` (no Pi base prompt),
  `inheritProjectContext/GlobalContext/Skills: false` (no AGENTS.md, no skills
  catalog), `extensions:` empty (no Superpowers in the child; pi-subagents warns
  about this on every launch — intended), `tools:` the seven file tools, and
  `excludeTools: contact_supervisor` (pi-subagents injects that tool and a
  supervisor-protocol prompt block into every child unless excluded; the
  supervisor protocol is what Mellum failed, measured in
  [ablation A8](ladder/ablation-a8-delegated-lean/README.md)), and
  `acceptance: level none` (the parent verifies by running the tests; an
  acceptance contract competed with the reply format and recorded a correct
  run as rejected). Nothing else: no `thinking:` (the level never reaches
  oMLX), no `allowedAgents:` (the child has no `subagent` tool to narrow),
  no `defaultContext:` (pi-subagents' default is `fresh`).
- `prompts/mellum-worker.md` (v5, 643 characters) — the body, duplicated
  into the agent file; a test keeps them identical. One line of role, six
  facts about the test command, one line for when the files cannot be found.
  *The task is complete only when the test command exits 0* and *if it
  fails, read the failure, change the code, and run it again* took rung 5
  from 0/3 to 3/3 ([phase 0b](ladder/phase0b-baseline-v3/README.md)).
  v3's six-step procedure and five tool descriptions were measured and
  removed ([A2](ladder/ablation-a2-v4a/README.md), [A3](ladder/ablation-a3-v4b/README.md));
  the missing-files line stays because the run without it edited a test
  ([A4](ladder/ablation-a4-v4c/README.md)).
- `extensions/mellum-guards.ts` — the child's guards, loaded only through the
  agent file's `subagentOnlyExtensions`. It lives outside `.pi/extensions/`
  on purpose: Pi auto-loads that directory into every session in a trusted
  project, parent included. On by default: the empty-final nudge (cap 3)
  and the loop breaker (five unbroken repeats of one call, forgotten after
  any edit, write, or bash call). Dormant: new-file-only `write`, step
  budget. See §6.
- No parent-side skill. One existed; it was read in 2 of 15 runs and the
  pass rate was 15/15 with or without it ([phase 3b](ladder/phase3b-delegated-skill/README.md)),
  so it was removed. Its content is §4's one paragraph on briefing.
- Optional, global to your profile: `{"intercomBridge": {"mode": "off"}}`
  in `~/.pi/agent/extensions/subagent/config.json` removes the 1,582-character
  supervisor block pi-subagents puts in every child's prompt; the worker
  passed 15/15 with it off and its prompt halved
  ([A11](ladder/ablation-a11-delegated-nointercom/README.md)).
  Every other subagent of yours loses `contact_supervisor` too, so only if
  none of them needs it.
- `~/.pi/agent/models.json` omlx entry must set `supportsDeveloperRole: false`:
  Pi otherwise sends the instructions as a `developer` message for a
  reasoning model on a localhost provider, and the mode replaces either
  role but older versions of the filter did not. Also `contextWindow 56000`, `maxTokens
  16384`, `thinkingFormat: qwen-chat-template`.

Try it safely: the setup skill's phase 7 copies a disposable fixture.

## 4. Using Mellum Worker (delegated)

In a normal Pi session, name the worker: "Use mellum-worker to do this: …".
Your parent scopes the task, writes the brief, launches the child, and — in
every measured run — runs the tests itself before reporting. The child's
one recorded pathology is a turn that ends with `stop` and no text;
pi-subagents reports it as "Subagent produced no output". In sixty
delegated runs the parent re-dispatched on that error and the run then
passed ten times out of eleven; the one miss was reported as blocked, never
as done ([A9](ladder/ablation-a9-delegated-final/README.md)).

The ladder's five sentences, as a user would type them, and what happened:

| rung | sentence | worker alone, prompt v3 (direct, greedy; cap 4,096 / cap 16,384) | via your Pi (delegated, prompt v3) |
| --- | --- | --- | --- |
| 1 | the cart total ignores quantity, fix it | 3/3 / 3/3 | 3/3 |
| 2 | add a balance() that sums the entries, with a test | 3/3 / 3/3 | 3/3 |
| 3 | rename fetch_rows to load_rows everywhere | 3/3 / 3/3 | 3/3 |
| 4 | make the failing test pass (three failing tests, three files) | 2/3 / 2/3 | 3/3 |
| 5 | the export is missing the totals row (same, plus a decoy, no test named) | 2/3 / 3/3 | 3/3 |

The worker as it ships, prompt v5, delegated: 3/3 on every rung, no
re-dispatch, no empty child turn ([A10](ladder/ablation-a10-delegated-v5/README.md)).

Mellum as the *primary* agent in your own profile, given the same sentences
([phase 0c](ladder/phase0c-primary-operator/README.md)): 3/3, 2/3,
3/3, 2/3, 0/3. It reads and follows the Superpowers skills; it fails when a
skill asks a question nobody answers, when a turn ends empty, and on the
three-file change by symptom. Bare Pi with no extensions or skills
([phase 0c plain](ladder/phase0c-primary-plain/README.md)): 3/3, 3/3,
2/3, 0/3, 0/3, with four empty finals, three false "fixed" claims, and one
rewritten test file. The worker alone, same model and harness but greedy
decoding and the worker prompt, is 15/15
([phase 2b](ladder/phase2b-guards-bounded/README.md), [A2](ladder/ablation-a2-v4a/README.md),
[A3](ladder/ablation-a3-v4b/README.md)); only the delegated runs
measure it at the sampling your Pi actually uses.

Where it stops working: rung 5 is a three-file change described only by a
symptom. Alone, the worker's failures there are honest ("tests still
failing") or silent (empty final). With a parent that scopes first, it
passes. A parent that reads the worker's reply will see either the test
output pasted, or "produced no output"; on the second, dispatch once more.

What it costs. Wall seconds are from an uncontrolled clock; "prefill" is
the characters the local server receives per run. On oMLX most of it is
cache hits (86% of the worker's input tokens in direct mode), so prompt
length is a token cost more than a wall-clock one. Fifteen runs each; full tables in
[ablation-summary.md](ladder/ablation-summary.md).

| setup | pass | wall s | Mellum requests per run (max) | prefill, k chars per run |
| --- | --- | --- | --- | --- |
| bare Pi, Mellum as the agent | 8/15 | 51 | 13.1 (30) | 297 |
| your profile, Mellum as the agent | 10/15 | 72 | 13.7 (26) | 1,055 |
| worker alone (direct, v5) | 15/15 | 54 | 14.3 (27) | 308 |
| worker via your Pi (delegated, v5) | 15/15 | 54 | 11.1 (16) | 221 |

| wall s per rung | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| bare Pi | 14 | 39 | 22 | 53 | 128 |
| your profile | 55 | 81 | 54 | 84 | 85 |
| worker alone | 18 | 36 | 21 | 87 | 108 |
| delegated | 30 | 38 | 24 | 77 | 99 |

Read it as: running Mellum in your full profile is the slow way (three to
four times bare Pi on the easy rungs, five times the prefill, from the 17k
character system prompt and skill files on every request); the worker
alone costs about what bare Pi costs and passes; delegation adds 10–15 s of
parent work on the small rungs and gives it back on the three-file ones,
where the briefed child needs fewer requests (14 vs 20) and never more than
16. Request counts are 11–14 per run everywhere; what differs is what each
request carries. The options for cutting this further, measured and
projected, are in [2026-10-09-worker-cost-options.md](superpowers/research/2026-10-09-worker-cost-options.md).

## 4b. The second way: Mellum Worker in your own session

**Mellum Worker** (`extensions/mellum-worker.ts`) turns your current session
into the worker without a parent, a brief, or a subagent.

Mellum Worker loads with the package; no `-e` flags. Type `/mellum <task>`: the session switches to Mellum, runs the task, and
switches back when the agent settles. For a longer back-and-forth use
`/mellum on`, type as many prompts as you like, and `/mellum off`. While the
mode is on, the model is Mellum, the tools are the worker's seven, and
every request is rewritten before it leaves: the system prompt is v5, the
messages are only those since `/mellum on` (Superpowers' bootstrap and
your earlier conversation are not sent), and pi-subagents' re-added tools
are removed. Your session keeps everything; after `/mellum off` your usual
model is sent one handoff block per span, on to off (a summary line with
the request count, output tokens, wall seconds and whether the last
command passed, failed or never returned; the first task; the files edited or written, flagged when
missing at handoff time; the last fifteen shell commands run, failed ones
marked; the last command output; Mellum's final reply) in place of
Mellum's reads, edits and test runs, which stay in the transcript. When
the mode switches off, Pi shows a one-line count of requests, tool calls,
output tokens and seconds, and one JSON line describing the span is
appended to `~/.pi/agent/mellum-mode-runs.jsonl` (`MELLUM_MODE_RUNS`
overrides the path; `0` disables it). Schema 2 adds files missing at the
end, which commands change files, the final turn's shape, nudge and
guard-block counts, activation, host, and package and prompt versions;
the file is append-only across upgrades, so lines without a `schema`
field are schema 1.
In the probe this took the parent's next request from 18 messages to 3.

Measured in the ladder ([A14](ladder/ablation-a14-mellum-mode/README.md),
before project facts existed), same profile and sampling as "Mellum as the primary agent" above: 10/15
becomes 14/15, rung 5 from 0/3 to 3/3, the model reads 606 characters of
prompt instead of 17k, and the wall time is the same (prefill is cached;
the time is generation). What you give up against delegation is the
parent's independent test run afterwards; run the tests yourself.

Where the cost goes, measured per task at the same sampling
([A10](ladder/ablation-a10-delegated-v5/README.md) vs [A14](ladder/ablation-a14-mellum-mode/README.md)):

| per task | Mellum Worker | Mellum Worker |
| --- | --- | --- |
| passes | 15/15 | 14/15 |
| wall, mean (by rung) | 54 s (30 / 38 / 24 / 77 / 99) | 70 s (24 / 76 / 31 / 99 / 122) |
| Mellum requests per run | 11.1 | 13.1 |
| your main model per run | 6.5 turns, about 3k output and 120k mostly cached input tokens | none |
| left for your main model | the parent's reads and the child's short report | one handoff block per task (the transcript keeps the detail) |

The Worker is not cheaper; its cost moves to your main model. The parent
reads the files, runs the tests once, writes the brief, and runs the tests
again on the result. That scoping is why the child needs 11 requests
where the Mode's model, starting from your sentence, needs 13 and thinks
longer per turn, and why the Worker is slower on a one-line fix and
faster on anything touching several files. Choose by what you are
protecting: the hosted model's tokens (Mode spends none), or wall time on
multi-file tasks (Worker). Both leave the main conversation a short
summary: the Worker's parent writes one, the Mode's handoff block is one.

**Project facts.** Mode reads the `## Mellum` section of `AGENTS.md` in
the working directory once per span, and appends its bullets (any label;
`Test command:`, `Write only:` and `Do not:` are the measured ones) as
`Project facts:` to every user message it sends, so the prompt's "a
command named in the task is the command" rule sees your test command.
The section ends at the next `#` or `##` heading and is capped at 600
characters of bullets; over that, Mode warns and ignores it. With no
`Test command:` bullet and a `pyproject.toml` that mentions pytest, Mode
adds `uv run --offline python -m pytest -q`. `MELLUM_MODE_FACTS=0` turns
both off. The session shows `[mellum-worker on] facts: <source>` when a
span starts, and the run record's `facts` field and the handoff summary
line name the same source (`agents-md`, `detected`, `agents-md+detected`,
`none`, `off`). The prompt is unchanged (v5). Write the label as plain
`Test command:` and the command as plain text (no bold or code formatting
on either): Mode recognises the test command only from a bullet whose
label is exactly `Test command:`. `- **Test command:** make test` is not
recognised, so in a pytest project Mode adds the fallback as a second test
command, and a backticked command keeps its backticks.

Measured on rungs 6–9 (AgentClinic: build a FastAPI app from four loose
phase specs, one phase per rung, three runs each, 600 s deadline; a run
passes when the project's tests and hidden behaviour tests pass, no
existing test was removed or edited, and nothing was written outside the
`AGENTS.md` write-list), Mode at prompt v5 with guards, 12 runs per
condition ([A18](ladder/ablation-a18-agentclinic-facts-off/README.md)
facts off, [A19](ladder/ablation-a19-facts-on/README.md) the section,
[A20](ladder/ablation-a20-facts-fallback-only/README.md) the section
stripped so only the fallback is sent):

| rungs 6–9 | facts off (A18) | section (A19) | fallback only (A20) |
| --- | --- | --- | --- |
| passes (rung 6 / 7 / 8 / 9) | 1/12 (0 / 1 / 0 / 0) | 9/12 (3 / 3 / 2 / 1) | 7/12 (1 / 2 / 3 / 1) |
| requests per run, median (mean) | 50 (54) | 26 (32) | 28 (37) |
| wall s per run, median (mean) | 261 (316) | 106 (163) | 143 (195) |
| output tokens per run | not in `run.json` | not in `run.json` | not in `run.json` |
| runs with `No module named 'app'` | 11/12 | 0/12 | 5/12 |
| runs that wrote outside the write-list | 8/12 | 0/12 | 5/12 |
| runs cut at the deadline | 3/12 | 1/12 | 1/12 |

A18 ran under a strict rule (every starting test file byte-identical,
0/12) and is shown rescored under the added-tests rule A19 and A20 use.
Wall is the runner's untrusted clock, with deadline runs at 600 s;
`run.json` records requests and wall time, not output tokens. On rungs
1–5, A19 passes 15/15 (A17, Mode as shipped in v0.1.2: 14/15) at a mean
of 13.8 requests (12.9) and 51 s (44 s); rungs 2–5 got the fallback,
rung 1 (Node) nothing.

What the numbers say: with the section, the first pytest command of all
12 runs was the forwarded one and the import error did not occur. The
fallback alone recovers 75% of the gain ((7 − 1) / (9 − 1)); in A20 the
five runs that ran the prompt's default first are the five with the
import error, and four of them failed with write-list entries. Not
fixed by facts: all four rung-9 failures in A19 and A20 broke the
phase-4 id rule (checked by rerunning the hidden tests), and every
rung-8 run in all three phases tried `from fastapi import
RedirectResponse`. Three repeats per rung; per-rung results are not
stable estimates. The verdict and the rest are in the
[research note](superpowers/research/2026-10-09-m7-project-facts.md).

Cautions. The ladder measured the headless path; the interactive path
(`on`, a second `on`, a task, `off`, a parent turn, a second `off`, the
one-shot form) was verified over Pi's RPC mode with `ladder/ladder/probe_mode_rpc.py`,
which showed each request carrying exactly the
expected prompt, history and tools. That probe predates project facts and
used the Node calculator fixture: facts were measured headless only, and
the interactive facts path (`/mellum on`, `/mellum <task>`, the
`[mellum-worker on] facts:` line, the handoff's `facts:`) is unit-tested, not
yet observed in a real Pi session (a probe on a Python fixture such as
agentclinic-p1 would observe it). The refusal to auto-compact while on
is unit-tested. Mellum Worker is loaded as a package extension; its payload filter rewrites the request it sees, and other packages' hooks may run before or after it. Load order was only verified for the `-e` form in the ladder. None of
Superpowers, pi-subagents or context7 rewrites the payload today. Auto-compaction is refused while the mode is on
(`/compact` still works); run `/mellum off` before a long parent turn.

## 4c. Records, learn and check

Every Mode span appends a record (§4b). `/mellum learn [n]` and
`node <package dir>/scripts/mellum.mjs learn` read the last n records for
the current directory, no model call, and count seven patterns from these
fields: `cwd`, `endedAt`, `requests`, `commands[]` (`command`, `failed`,
`mutates`), `files`, `lastCommand`, `finalReply`, `finalTurn` (`hadText`,
`hadToolCall`) and `server`. A record without `kind` is a Mode record.

Two files hold records. Mode appends `kind: "mode"` records to
`~/.pi/agent/mellum-mode-runs.jsonl` (`MELLUM_MODE_RUNS`). The Pi Worker
appends `kind: "worker"` records to `~/.pi/agent/mellum-worker-runs.jsonl`
(`MELLUM_WORKER_RUNS`; `0` or empty disables it). `learn` reads both. A Worker
record is schema 2 with `activation: "worker"` and `facts: null` (the
Worker gets no project facts); `host` comes from Pi's mode, `promptVersion`
from the child's system prompt (the marker is found on any line, after
pi-subagents' preamble), and `server` from the same 1,000 ms settings check
as Mode. `extensions/mellum-guards.ts` writes it inside the pi-subagents
child, one line per finished run; a child killed before it settles writes

Records written after 0.1.6 also have `toolCalls` (count per tool name),
`toolErrors` (tool results marked as errors, any tool) and
`firstWriteSeconds` (first assistant turn to the first `edit` or `write`;
absent without one). `/mellum last` and `node <package dir>/scripts/mellum.mjs
last` show the newest record for the current directory as a Markdown table;
older records show dashes for these three.

| pattern | fires when | suggests |
| --- | --- | --- |
| `test-thrash` | two or more runs failed a test command first, then passed another | `Test command:` with the one that passed |
| `bent-project` | a run wrote `__init__.py`, `pytest.ini`, `setup.cfg`, `pyproject.toml`, `uv.lock`, a root `conftest.py`, or ran `pip install`, `uv add`, `uv pip` | `Do not:` with one value per kind of bend seen: install packages or add dependencies; add `__init__.py`, `conftest.py`, `pytest.ini` or `setup.cfg` files |
| `false-success` | the reply claims success but the last command did not pass | nothing; run the tests yourself |
| `long-run` | a run took more than 30 requests | nothing; split the task |
| `servers` | a run started a server | `Do not: start servers` |
| `drift` | the record's `server.match` is false | nothing; run `/mellum check` |
| `announce-stop` | the final turn had text and no tool call, and the last command did not pass | nothing |

The suggestion is a `## Mellum` section of the bullets in [Project
facts](../README.md#use-it): shown first, written to `AGENTS.md` only after
a yes, only the missing lines, never past the 600-character cap, and a line
you have with another value is reported as a conflict, not rewritten.
The thresholds are judgement on little data; each message states its count.

`/mellum check` and `scripts/mellum.mjs check` read `/v1/models`,
`/admin/api/models` and `/admin/api/global-settings` (GET only) and your
provider entry, and report `server`, `model`, `settings`, `global`,
`provider`, `advice` and `admin` findings, worst first. The expected values
are in `templates/omlx-model-settings.json`. A `settings` difference fails
when no request can undo it: a `serverOnly` key (context window, TurboQuant,
thinking budget, tool-result cap; a test ties all but TurboQuant, which the
ladder never set, to its baseline profile), thinking forced off (`forced_ct_kwargs` lists `enable_thinking`
and the server's `enable_thinking` is false), or, with `force_sampling` on,
a temperature, top_p or top_k other than `forcedSampling` (1 / 0.95 / 20,
what Pi sends). A difference in `overridden` (`max_tokens`, thinking,
penalties), which each request sends, is info. The provider entry is
compared with the host's template; a different `maxTokens` or sampling
value fails, since that is what binds. A settings fix prints as the `PUT` to
run yourself. On each activation Mode reads the same binding settings (one
second at most, silent when unreadable) and warns once: `Mellum server settings differ:
<key> <actual> (expected <expected>). Run /mellum check.` The record's
`server` field (`match`, and the differing keys) lets `learn` tell a run on
drifted settings apart later.

## 5. Measuring

Measurement lives in `ladder/` in this repo: `cd ladder && uv run python -m ladder.run_ladder --help`. The installed package is the result; `ladder/` is the ruler.
Use `--pi-executable /absolute/path/to/pi` to select an isolated runtime
for research; the ladder records its version and verifies each fixture
environment before launching. Delegated children use the same selection.

## 6. What is settled and what is not

Settled by measurement:

- The worker prompt's two completion facts were the lever (11/15 → 15/15).
- Of the settings, only the request cap has a measurable effect (it is a
  request value, sent by Pi); the penalty, thinking budget and tool-result
  cap do not, with the caveat that 1c→1d changed the cap and the penalty
  together ([1c/1d](ladder/phase1d-tuned-effective/README.md)).
- No `write` shrank an existing file and no test file was edited in 240
  direct runs except one (A4, reverted). The loop breaker as shipped
  (repeats forgotten after any edit, write, or bash call), replayed over
  all 330 runs, would have refused nothing; its earlier form refused one
  legitimate re-read after an edit in two passing runs and was corrected.
- A frontier parent scopes and verifies natively; the child never needs the
  user's sentence.

Not settled:

- The empty-final nudge, capped at 3 with the loop breaker live, in direct
  mode: 15/15, seven nudges in six runs, every nudged run green
  ([phase 2b](ladder/phase2b-guards-bounded/README.md)); without
  the extension, 13/15 ([A1](ladder/ablation-a1-noguards/README.md)).
- **The nudge does not fire inside a pi-subagents child.** Zero nudges in
  sixty delegated runs while eleven children "produced no output"; the
  parent's re-dispatch is what recovers them. Retired with the Worker (M.12).
- The Markdown brief as a mediator: chunked into one prompt per step it
  passes everything at 2.4× the cost; as one prompt with step-wise
  "reply" instructions it drops to 11/15 because the model stops at the
  first reply ([A15/A16](ladder/ablation-a15-chunked-brief/README.md)).
  The sentence plus the worker prompt stays the cheapest reliable input.
- pi-subagents appends an "Intercom orchestration channel" block (about
  1,500 characters) to the child prompt even with `contact_supervisor`
  excluded; `intercomBridge.mode: off` removes it ([A11](ladder/ablation-a11-delegated-nointercom/README.md)).
- Mellum as the primary agent is viable through rung 4 (10/15 overall) and
  fails rung 5; the worker's gain is at the top of the ladder, not an escape
  from a broken primary mode.

Follow-ups and the research record: [docs/superpowers/research/](superpowers/research/) and the phase records in [evals/](ladder/).
