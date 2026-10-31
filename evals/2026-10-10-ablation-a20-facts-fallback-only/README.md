# A20: Mellum Mode on the AgentClinic rungs, fallback command only (M.7)

**What is measured.** A19's launch on rungs 6–9 with the `## Mellum` section
removed from each workspace's `AGENTS.md` before the run
(`--strip-facts-section`), so Mode finds no section and forwards only the
detected fallback, `Test command: uv run --offline python -m pytest -q`: no
write-only list and no do-not line. Checked in every trace: one `Project
facts:` block per request carrying that one bullet. Mode at commit `aff031a`
(`worker_git` `v0.1.2-40-gaff031a`, prompt v5), guards on, three repeats per
rung. This is what a Python project without the section gets.

It answers two comparisons on rungs 6–9: against
[A18](../ablation-a18-agentclinic-facts-off/README.md) (facts off; 1/12
rescored, median 50 requests) and against [A19](../ablation-a19-facts-on/README.md)
(the full section; 9/12, median 26). Scoring is spec §2 rule 3 as changed by
Paul (additions to tests allowed), the same rule as A19 and A18's rescore.
A20 informs the docs and does not gate the ship rule.

Launch, 2026-10-10 08:56 EDT, from `ladder/` at commit `aff031a` (finished
09:35 EDT, 12 rows):

    uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 6 --rung 7 --rung 8 --rung 9 --repeat 3 --deadline 600 --strip-facts-section --out ../evals/2026-10-10-ablation-a20-facts-fallback-only

oMLX was up; `~/.pi/agent/mellum-mode-runs.jsonl` had 7 lines before and 7
after.

## Result

| rung | A18 rescored | A20 | A19 | A20 requests, median (runs) | A20 wall s, median (runs) |
| --- | --- | --- | --- | --- | --- |
| 6 (phase 1, home) | 0/3 | 1/3 | 3/3 | 25 (27, 25, 20) | 91 (91, 600, 39) |
| 7 (phase 2, board) | 1/3 | 2/3 | 3/3 | 27 (55, 23, 27) | 85 (174, 73, 85) |
| 8 (phase 3, add) | 0/3 | 3/3 | 2/3 | 29 (23, 38, 29) | 113 (112, 173, 113) |
| 9 (phase 4, resolve and reopen) | 0/3 | 1/3 | 1/3 | 53 (72, 53, 51) | 312 (336, 233, 312) |
| all | 1/12 | **7/12** | 9/12 | **28** (mean 37); A18 50, A19 26 | |

The fallback alone recovers 6 of the 8 passes A19 gains over A18:
(7 − 1) / (9 − 1) = 75%. One run hit the 600 s deadline (rung 6 r2).

## Per run

`wp` is `outside_write_list`; `facts` is `facts_cmd_pass`; `hid` is
`hidden_pass`; `kept` is `tests_unchanged` under rule 3; `first` is the first
pytest command the run issued.

| run | pass | requests | wp | facts | hid | kept | first |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 r1 | no | 27 | `pyproject.toml`, `uv.lock` | yes | yes | yes | fallback |
| 6 r2 | no | 25 | `__init__.py` | no | no | yes | prompt default |
| 6 r3 | yes | 20 | none | yes | yes | yes | fallback |
| 7 r1 | no | 55 | `__init__.py`, `pytest.ini` | yes | yes | yes | prompt default |
| 7 r2 | yes | 23 | none | yes | yes | yes | fallback |
| 7 r3 | yes | 27 | none | yes | yes | yes | fallback |
| 8 r1 | yes | 23 | none | yes | yes | yes | fallback |
| 8 r2 | yes | 38 | none | yes | yes | yes | fallback |
| 8 r3 | yes | 29 | none | yes | yes | yes | fallback |
| 9 r1 | yes | 72 | none | yes | yes | yes | prompt default |
| 9 r2 | no | 53 | `conftest.py` | yes | no | yes | prompt default |
| 9 r3 | no | 51 | `__init__.py`, `pytest.ini` | yes | no | yes | prompt default |

"Fallback" is `uv run --offline python -m pytest -q`; "prompt default" is
prompt v5's `uv run --offline pytest -q`.

## Failure shapes

- **Five runs ran the prompt's default instead of the forwarded command.**
  6 r2, 7 r1, 9 r1, 9 r2 and 9 r3 issued `uv run --offline pytest -q` first,
  with the fallback in every request, and each got `No module named 'app'`
  (2 to 11 tool results per run). Four of the five failed; 9 r1 passed after
  72 requests. Of the seven runs that ran the fallback first, six passed.
  Why the model chose the prompt's command over a forwarded one that differs
  by `python -m` was not checked; all three rung-9 runs did.
- **The write-list fixes return with the import error.** Four of the five
  write-list failures follow it: `__init__.py` (6 r2, 7 r1, 9 r3),
  `pytest.ini` (7 r1, 9 r3), `conftest.py` at the root (9 r2). All five
  prompt-default runs also tried package installs (`uv pip install`,
  `pip install .`, `pip install -e .`, `uv install .`); the do-not bullet was
  among the stripped lines.
- **9 r1 installed into the ladder's own virtualenv.** Bare `python` in the
  run's shell resolves to `ladder/.venv/bin/python` (the runner is launched
  with `uv run`), outside the workspace. 9 r1 ran `python -m ensurepip` and
  `python -m pip install starlette` and `httpx2` there (`httpx2` was
  downloaded, not from the offline cache), then passed with `PYTHONPATH=. uv
  run --offline pytest -q` in the workspace's own environment. The scorer
  sees only the workspace, so the write-list does not catch this; the
  ladder's virtualenv kept those packages after the phase. A18 9 r3's
  installs went into the workspace's `.venv`.
- **6 r1: a dependency added up front.** It ran the fallback, but before
  running any test added `jinja2` to `pyproject.toml` (the lock changed with
  it); project and hidden tests passed, the write-list failed it.
- **7 r1: green but outside the list.** Project and hidden tests passed; the
  run failed only on `__init__.py` and `pytest.ini`.
- **6 r2: a missing annotation, then the deadline.** `def home(request)` with
  no `Request` type makes FastAPI read `request` as a query parameter, so `/`
  returns 422 (checked by rerunning the hidden test in the retained
  workspace). The run then started uvicorn in the foreground on ports 8000,
  8001 and 8002; each exited at once with `[Errno 48] Address already in
  use`, because servers left by earlier deadline runs held them (see Risks).
  The fourth start, on 8003, has no result before the 600 s deadline; that
  it held the run is inferred from the trace, and it too was left running.
- **9 r2 and 9 r3: complaint ids, as in A19.** 9 r2 made `id` the first
  positional field (`Complaint("a", "b")` raises a missing `text`
  argument); 9 r3's new complaints both get id 0 (`assert 0 != 0`). Checked
  by rerunning the hidden tests in the retained workspaces.

## What is conjecture

That the remaining gap to A19 (7/12 against 9/12; five write-list entries
against none) comes from the missing write-only and do-not bullets rather
than from the fallback command's wording. The import error, not the absent
list, is what preceded four of the five write-list entries, so a stated
command the model actually uses may matter more than the list itself.

## What would falsify this

A repeat landing at or below A18 (1/12) would show the fallback is not
worth shipping on its own. A repeat in which every run uses the fallback
first and the write-list still fails would show the list, not the command,
is what A19 added.

## Risks

- Three repeats per rung; the 75% share rests on 7 of 12 and 9 of 12.
- The fallback and the prompt default differ by two words; this phase cannot
  say whether a more distinct command would be followed more often.
- A run's shell can reach the ladder's own virtualenv (9 r1 above), so a
  run can change the harness's environment for the runs after it. The
  scorer runs the workspace's environment, so A20's scores are not affected
  as far as checked, but later phases should start from a clean
  `ladder/.venv`.
- Runs share the machine's ports, and the runner does not stop leftover
  servers. Every run that hit the 600 s deadline in A18, A19 and A20 (A18 6 r2, 8 r1, 9 r1; A19 8 r2; A20 6 r2) ended on a server
  started in the foreground, and the runner left it running when it cut
  the run, on ports 8000 to 8003 (A19 8 r2's on `*:8001`, the port
  oMLX serves on at 127.0.0.1). A later run that starts a server meets
  them. Scores are not affected (both affected runs fail for their own
  reasons), and the controller stopped those servers on 2026-10-10 about
  09:50 EDT, after the phases.

Raw traces, stdout and diffs: [`ablation-a20-facts-fallback-only.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a20-facts-fallback-only.tar.gz)
(sha256 `b549e06a201fbffdd0badb268cb52ee6eaec4ab9ce90ffa74796962fdc3e84d0`).
