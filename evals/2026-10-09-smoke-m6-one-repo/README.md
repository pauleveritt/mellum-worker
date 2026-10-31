# Smoke M.6: one rung-1 Mellum Mode run from this checkout

**What is measured.** That the ladder, now in this repository, launches a real
Mellum Mode run against the local oMLX server and measures this checkout's
extension, prompt and guards, not a copy somewhere else. One run, rung 1
("the cart total ignores quantity, fix it"), baseline profile, mode `mode`.
Run on 2026-10-09 from commit `e5e72f3`.

**What is conjecture.** Nothing here estimates a pass rate. One run proves the
launch, not the pass rate.

## Command

    cd ladder && uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 1 --repeat 1 --deadline 600 --out ../evals/2026-10-09-smoke-m6-one-repo < /dev/null

## The four checks

| check | expected | observed |
| --- | --- | --- |
| rung result | pass, tests unchanged | pass, `tests_unchanged` true, stop reason `stop` |
| `requests` in `run.json` | 7 to 9 (A17's rung-1 range) | 7 |
| `worker_git` in `run.json` | non-empty | `v0.1.2-27-ge5e72f3` (`worker_version` 0.1.2) |
| first `provider_request` in `trace.jsonl` | one `system` message starting `<!-- mellum-worker prompt v5 -->`; 7 tools | one system message, starts `<!-- mellum-worker prompt v5 -->`; 7 tools: `read`, `grep`, `find`, `ls`, `bash`, `edit`, `write` |
| `~/.pi/agent/mellum-mode-runs.jsonl` line count | unchanged by the run | 7 before, 7 after |

Wall time was 9 s untrusted, 0 tool errors, 0 nudges, largest prompt 11861
characters. The run's tool calls were `ls` 1, `read` 3, `edit` 1, `bash` 1.

## What would falsify this

A first request with two system messages or a tool list of other than seven
would mean the extension loaded twice or from the profile instead of this
checkout. A run-log line count that grew with a `cwd` inside a `ladder-`
scratch directory would mean the run log was not isolated.

## Risks

- One run on one rung: it cannot show that the move changed no behaviour,
  only that nothing is broken at launch.
- The server may have been in use by something else; wall time is untrusted.

The run is in `rung1-baseline-mode-guards-r1/` (`run.json`, `final.md`) with
`table.md`.

Raw traces, stdout and diffs: [`smoke-m6-one-repo.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/smoke-m6-one-repo.tar.gz).
