# Easy ladder: build a pass from Vanilla Pi, one explicit unit at a time (2026-11-02)

## What is measured / what is conjecture

**Measured:** the Easy challenge suite on the real local model (Mellum2.1-12B-A2.5B
Q4_K_M, llama-server :8001), each config n=3, `--grade`, from a true floor —
`--arm vanilla` (recorder only, no worker extension) — with each unit added
explicitly through `--remedy`. **Conjecture:** the two theories at the end; they
are not yet run.

## Why

The worker is a bundle (prompt, four guards, facts, tool-narrowing) switched on by
`MELLUM_MODE`. To know what actually earns a pass, start from nothing and add one
inspectable unit at a time, reading the model's own feed on each run — not the
bundle.

## Measured so far (Easy, n=3)

| Config | Pass | Notes |
| --- | --- | --- |
| `vanilla` (recorder only) | fail | the floor |
| plain worker — `preset:baseline-worker` (6 units, **no prompt**) | **0/3** | flailed ~15 turns shelling `find`/`ls` through `bash` (no search tool was offered — see below), then invented the layout (`main.py`, no templates) |
| `arm:worker` (full worker, **with** the worker prompt) | 2/3 | 53–64 turns |
| `vanilla + prompt/name-the-layout` | **2/3** | one agnostic line ("take the layout from the spec"); fastest pass **15 turns** |
| `vanilla + name-the-layout + guard/repeat-loops` | 2/3 | `repeat-loops` fired **0 times**; no change |
| `vanilla + name-the-layout + prompt/python-developer` (n=3) | 3/3 | 20 · 19 · 14 |
| `vanilla + name-the-layout + prompt/python-developer` (**n=6**) | **4/6** | median 18 (15–28) |
| `vanilla + name-the-layout + python-developer + guard/foreground-server` (**n=6**) | **5/6** | blocking the server-start that stood in for a check moved one more rep across; within n=6 variance, a lead |

**Reading:** on Easy the lever is **guidance, not guards**. Two agnostic prompt
lines on Vanilla Pi reach a fast pass with no guards and nothing coded to the eval.
But **n=3 (3/3) was optimistic — n=6 is 4/6 (~67%)**: a strong lead, not a reliable
pass. The two failures are **different bugs with one common cause — no real
verification**: rep2 wrote `def home(request):` (missing `Request` → `GET /` 422)
and "verified" by starting a foreground server, which never hits the route; rep5
had the route correct but a different defect and just re-read the files before
declaring done. The `python-developer` prompt makes the model *attempt* care, but
"care" comes out as reading files or launching uvicorn, not running `GET /`. So the
reliability lever is **verification** (run the real route/test before finishing),
which would catch both; `tool/lookup-library-docs` (T2) only addresses rep2's class. The six guards+facts
got 0/3; one agnostic prompt line matched the whole worker's 2/3 and did it in 15
turns vs 53. The guards stop bad *actions* (hangs, loops); the failures here are
**inventing the wrong layout**, then — from the feed — **shipping a careless
`if __name__ == "main__":` typo unchecked** and **declaring "done" without
running the check**. A loop guard does not touch those.

## The tool set these runs actually ran on (measured, corrects an assumption)

Every one of the 26 easy-ladder runs — vanilla and each rung — was offered the
**same four tools**: `read`, `bash`, `edit`, `write`. Read straight from each
run's first `provider_request` in `trace.jsonl`; all 26 agree. `grep`, `find`,
`ls`, `glob` and `codemode` were **never offered** on any run, and `codemode`
and `glob` were **never used** because they were never there. Pi's full built-in
registry is nine tools, but five are off by default; `read, bash, edit, write`
is the whole default surface (it matches Pi's own tagline).

Two consequences for reading this ladder:

- **The worker's "tool narrowing" is a no-op here.** `WORKER_TOOLS` is seven and
  `context/narrow-tools` only *filters the offered list down* — with just the
  four already inside that seven, it removes nothing. Narrowing bites only when
  something upstream (a `--tools` flag or an extension) first *adds* grep/find/ls.
- **The model had no search tool on Easy.** The plain-worker flailing "on
  `find`/`ls`" was `find`/`ls` run **through `bash`**, not tool calls. The
  absence of a search tool is a plausible contributor to the wandering and the
  invented layout — untested here, a lead for a rung that adds a search tool.

## Theories (conjecture — to measure, not yet run)

- **T1 — a focused role prompt cuts careless failures. (SCREEN: supported, n=3.)**
  `prompt/python-developer` prepends "You are an experienced, meticulous python
  developer working in a spec driven paradigm." to the system prompt. **Measured
  2026-11-02:** `vanilla + name-the-layout + python-developer` went 2/3 → **3/3**
  on Easy at 14–20 turns. A screen on one tier on one local host — a strong lead,
  not a settled verdict; replicate before shipping a default.
- **T2 — look up the installed source when unsure of an API helps.** This is the
  existing, **already-built but unmeasured** `tool/lookup-library-docs`
  (`extensions/mellum-knowledge.ts` → `docs_lookup.py`): a BM25 index over the
  venv's package source, exposed as a `lookup` tool for API-shaped uncertainty.
  Prediction: on API-exact failures (e.g. a 307-vs-303 redirect) it is called and
  lifts the pass. Rung: add `tool/lookup-library-docs`, n=3. **Not a new unit —
  test the one that exists.**

## What would falsify this / risks

- n=3 on one tier on one host is thin; a 2/3 ↔ 3/3 swing can be variance. Treat any
  single rung as a lead until replicated.
- T1 risk: a role prompt may add turns (more deliberation) without changing the
  pass, or the gain may be the word "meticulous" doing nothing measurable — the
  turn count and the per-rep feed will show it.
- T2 risk: the model may never call `lookup` on Easy (Easy has no post-cutoff API),
  so a null on Easy does not clear it — it needs a rung whose failure is API-shaped.
- All prompt units must stay **agnostic** (no suite path, file or route); a unit
  that names the layout would be coding to the eval and is void as evidence.
