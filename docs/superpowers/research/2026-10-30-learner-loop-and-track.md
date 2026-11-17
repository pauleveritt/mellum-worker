# The learner loop and lesson track — clone, install, run, and a self-recording worker

Date: 2026-10-30. Lifecycle: design capture (direction, mostly conjecture — not
a measured result). Captures the architecture and lesson track sketched in
conversation on 2026-10-30, so the pieces are not lost before they are built.

## What is measured / What is conjecture

**Exists / measured already** (the loop leans on these):
- `install.sh` installs the toolchain (uv, llama.cpp `llama-server`, Node, Pi).
- `scripts/backend.py start` serves llama.cpp and is idempotent (returns 0 if
  already healthy); first start downloads the ~8 GB `Q4_K_M` model via `-hf`.
- Pi loads the mellum-worker harness as a plugin: `pi install git:…` (README).
- `/mellum <task>` runs a task and appends a JSON record per span to
  `~/.pi/agent/mellum-mode-runs.jsonl` (the recording foundation).

**Conjecture** (unbuilt direction): the end-to-end loop below, and the lesson
redesigns. None is screened yet.

## The runtime: clone → install → run

- **`install.sh`** (repo root): installs the tools, pins **Pi 1.3.0** (the
  version this repo is measured against), and gives base Pi the **harness
  abilities** (`pi install git:…` so the learner's Pi has the worker prompt,
  guards, remedies — not bare Pi). Then **hands off to `run.sh`**.
- **`run.sh`** (repo root): start the server + model (`backend.py start`,
  idempotent) and launch the **harnessed Pi**. Next time the learner comes
  back, they just `bash run.sh`.
- The learner **chats with the harness** to make things happen (`/mellum
  <task>`, the S0-guided process below).

## North star: a self-recording worker that opens PRs

Everything the worker does is recorded (mellum-mode run records, `run.json`,
traces). The aim: the local Mellum + Pi combo **solves the lessons' and
challenge's problems, records the findings, and opens pull requests up to
`andrevanzuydam/mellum-worker` with those findings.** The recording exists; the
PR automation (auth, safety, what a "finding" PR contains, human review) is the
big future piece, built last.

## The lesson track (one pathology per lesson, forced on demand)

Current rule: each lesson's pathology is **produced on demand by a stated
condition**, before **FAIL** → after **PASS**, host-independent where possible;
FAIL may be read from the run record, not only hidden tests.

| # | Lesson | Pathology / condition | Remedy |
|---|--------|------------------------|--------|
| S0 | Start Here | Orientation, not a pathology: **guide the process** — how the learner chats with the harness (`/mellum`, `run.sh`, the loop) to make things happen. | — |
| E1 | Thinking window / token sizes | The model reasons first and the **tool call comes at the end**, so too small a `max_tokens` truncates before the tool call (`length`-stopped / empty final in `run.json`) → FAIL; too large wastes. **Lever: set `max_tokens` / thinking budget from Pi to the llama-server, per request.** Host-independent, so it **fixes the current E1** (reasoning-as-text) only failing on the LAN vLLM host. | reserve answer budget (cap thinking / floor the answer) |
| E2 | Project folder | Files get mixed up everywhere; the model **scans and writes across the whole computer**. Condition: a task in a shared / cluttered dir. | **keep a project folder** (`guard/stay-in-workspace`) — also stops scanning every file on the machine |

Other pathologies already drafted (slot as the track firms up): know-when-to-stop
(`guard/cap-turns`), too-many-tools (`context/narrow-tools`), the foreground-server
stall (`guard/block-foreground-server`), reading more than fits
(`context/trim-tool-output`).

## The token-size control (E1's lever, useful generally)

Pi must set `max_tokens` (and the thinking budget) **to llama-server, per
request** — the Pi provider entry carries `maxTokens`, and the harness can
override per request (`before_provider_request`). E1's challenge sets it **small
to force** the truncation; the remedy **reserves** answer budget. Confirm the
exact Pi mechanism when building E1 (and whether the thinking budget is set via
the chat template or a server flag).

## Build order (agreed 2026-10-30)

1. **Capture** — this note.
2. **Setup scaffolding** — `run.sh`, `install.sh` → `run.sh` handoff, harnessed Pi.
3. **E1** — the token-window lesson.

## What would falsify this / Risks

- The PR-with-findings loop is unbuilt and likely large (auth, safety, review);
  only the recording exists today.
- E1's token-window FAIL must be **shown** to truncate reliably on the default
  backend — screen it before claiming the lesson holds.
- Giving base Pi the harness by a global `pi install` couples the learner's Pi
  to the plugin; confirm it does not break the lessons that need **bare** Pi.
- `install.sh` now references repo paths (`scripts/backend.py`, the profile) via
  `run.sh`; it is no longer location-independent, which is fine as a repo-root
  script but must be run from the clone.
