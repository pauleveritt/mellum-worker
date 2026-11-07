# Phase 0: baseline profile, Pi direct mode

Date: 2026-10-08. Worker prompt v2, no guards. Model
`omlx/Mellum2.1-12B-A2.5B-Thinking-6bit` on oMLX 0.6.4 with the **baseline**
profile (`max_tokens 4096`, thinking budget off, presence penalty 0, no
tool-result cap — of which only the server-side settings were effective; see
the sampling note below). Pi 1.0.2 in the recovery report's clean profile
(`pi -p --mode json --no-extensions --no-skills --no-context-files --no-session
--thinking high --tools read,grep,find,ls,bash,edit,write
--append-system-prompt prompts/mellum-worker.md -e ladder/record-pi.js`).
All requests were sampled, not greedy: Pi sent `temperature 1`, `top_p 0.95`, `top_k 20`, `max_tokens 16384`, `presence_penalty 0` on every request, and oMLX gives request values precedence over the model profile. Three repeats per rung. 600 s deadline.

Command:

```bash
uv run python -m ladder.run_ladder --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase0-baseline
```

## Result

| rung | sentence | pass |
| --- | --- | --- |
| 1 | the cart total ignores quantity, fix it | 3/3 |
| 2 | add a balance() that sums the entries, with a test | 3/3 |
| 3 | rename fetch_rows to load_rows everywhere | 3/3 |
| 4 | make the failing test pass (three failing tests across three files) | 2/3 |
| 5 | the export is missing the totals row (same fixture plus a decoy, no test named) | 0/3 |

11 of 15. Full columns in [table.md](table.md); one directory per run with
`run.json`, `trace.jsonl` (every provider request and tool event),
`stdout.txt` (Pi's JSON event stream), `final.md`, and `diff.patch`.

## Non-zero pathology columns

| column | runs | what happened |
| --- | --- | --- |
| `empty_final` | 2 (4 r2, 5 r1) | The turn ended with `stopReason: stop` and no visible text. Not a token-budget death: the stop reason is `stop`, not `length`. This is satyrn-evals pathology 21, "announces the next action in its reasoning, then ends the turn without it". 5 r1 made two requests and stopped after reading. |
| `edit_anchor_failures` | 2 runs, 6 events | "Could not find the exact text" from Pi's edit tool; both runs recovered and passed (2 r2, 3 r1). |
| `write_existing` | 2 | Whole-file `write` to an existing file, in both cases growing it (test_ledger.py 7 → 12, export.py 5 → 10). `write_shrink` is 0: the fragment-as-whole-file clobber did not occur. |
| `tool_errors` | 7 runs | Mostly `bash` exits from failing tests before the fix, plus the anchor failures above. |
| `max_identical_streak` ≥ 5 | 0 | No repeat loops. Largest streak 2. |
| `bash_file_mutations` | 0 | No heredoc or redirect writes. |
| `deadline_hit` | 0 | |

Largest prompt: 50,471 chars (rung 5 r2) — under the 200,000-char (~50k token)
gate with room to spare, but note it is the rung that iterates most.

## How rung 5 fails

All three rung-5 failures are honest: the model reported the failing test
output verbatim and stopped after one edit cycle. 5 r2 fixed `export.py`
only (2 tests still failing); 5 r3 fixed `export.py` and `totals.py`
(1 failing, `render_rows` missing `mark_last`); 5 r1 stopped after reading.
The procedure in prompt v2 says "run the test command" once and does not
state that the task is complete only when the command exits 0. That is a
fact the prompt can supply (see the facts-not-rules decision in the spec);
it is a phase 1/3 candidate, not a baseline change.

Rung 4 r2 failed the same way: it changed `totals.py`, ran the tests
(`.FFF`), and ended with an empty reply.

## Attempt 1

`../phase0-baseline-attempt1/` is the first run of this phase with the
earlier rung 4/5 fixture, which had a single failing test that the model
solved correctly inside `export.py` alone (3/3 tests passed, the ≥2-files
check failed). That was a fixture flaw, not a model failure; the fixture was
rewritten so three failing tests span three files. Attempt 1's traces are
kept because they also show the empty-final pathology (3 runs) before the
runner recorded stop reasons.

## Versions

Pi 1.0.2; oMLX 0.6.4; live model settings at run time are in each
`run.json` under `versions.model_settings`. Pi's `~/.pi/agent/models.json`
omlx Mellum entry had `contextWindow` corrected from 131072 to 56000 before
this run (backup `models.json.bak-ladder-*`). Wall times are recorded and
untrusted (other processes shared the machine).

Raw traces, stdout and diffs: [`phase0-baseline.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase0-baseline.tar.gz).
