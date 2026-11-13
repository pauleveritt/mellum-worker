# Handover — prove each lesson (before FAIL → after PASS)

Working note for continuing the lesson-proof effort on a local machine.
Transient; delete when the effort lands. Updated: 2026-10-30.

## Where things stand

- **The rule changed.** A lesson's pathology must be produced on demand by a
  condition the lesson states; screen first; FAIL may be read from the run's
  record (`record.json` caps on `run.json` fields), not only hidden tests.
  Why: [lessons rethink](docs/superpowers/research/2026-10-29-lessons-rethink.md);
  the luck-dependent lessons that left the track:
  [note](docs/superpowers/research/2026-10-29-lessons-left-the-track.md).
- **One session per arm** (lessons do not need n = 3), preregistered before
  the deciding run.
- **Two lessons hold** (checkpoint `checkpoint-2026-10-30-first-lesson-holds`
  after E1; E2 at `8b8341f`):

| Lesson | Condition | Before | After |
| --- | --- | --- | --- |
| E1 Reasoning Returned as Text | LAN vLLM's parser misses streamed follow-ups | FAIL, `reasoning_as_text` 7 | PASS, 0 (`context/repair-think-tags`) |
| E2 Reading More Than Fits | 8 × 40 KB notes against a 64k window | FAIL, 13 compactions | PASS, 0 (`context/trim-tool-output`) |

  Records: `evals/2026-10-30-reasoning-as-text-check/`,
  `evals/2026-10-30-context-overflow-check/`; preregistrations in
  `docs/superpowers/research/2026-10-30-*-prereg.md`.

## Open issue: E1 does not fail on oMLX

E1's condition is the **host**, not the task. The LAN vLLM build
(`0.26.1rc1.dev1102`) returns reasoning as `<think>` reply text after the
first turn (236 of 244 turns). oMLX returns Mellum's reasoning in its own
`reasoning_content` field (recorded in
`docs/superpowers/research/2026-10-07-mellum-recovery/opencode-report.md`),
as does pinned vLLM 0.32.0 (0 of 136). So a learner on oMLX — the README's
default backend — would see the before arm PASS and nothing to repair. The
page's front matter already says `backends: [vllm]`, but the track puts E1
first for everyone. Not yet screened on oMLX; the above is from the record.

Two options, undecided:

1. **The challenge injects the fault** (recommended): a challenge-owned
   extension moves the reasoning back into the reply as `<think>` text after
   the first turn, standing for a misparsing server or bad chat template. The
   before arm then fails on any host. Check first that the repair runs after
   the injection (Pi's extension load order on `message_end`), then screen it.
   The page says the fault is staged and how to check your own host
   (`reasoning_as_text` in a bare run).
2. **Drop E1 from the track** to a host note; E2 becomes E1.

E2 is unaffected: oMLX's window is 56,000, so the notes overflow it sooner,
and the E1 repair is a no-op on a correct host.

## Next on the track

- Decide E1 (above).
- Screen the next Easy candidate: **thinking spends the output cap** (a small
  `max_tokens` in the profile; record empty or `length`-stopped finals in
  `run.json`; remedy reserves answer budget via `before_provider_request`).
  Then runaway turns (`guard/cap-turns`).
- E3 Looking Around, E4 Searching, E5 Creating Files, E6 Too Many Tools still
  have no condition that produces their failure: find one (screen it) or they
  leave the track. Medium (task traps) and Hard (orchestration) candidates
  are in the rethink note. `PENDING` in `tests/lesson-contract.test.mjs` may
  only shrink.

## Run a lesson check

```bash
scripts/lesson-check.sh E2            # detached; log in runs/<n>-check-*/check.log
scripts/lesson-check.sh E2 --dry-run  # print the two lines the page holds
```

Default profile `scripts/baseline/lan-profile` (6-bit Mellum on
`http://192.168.88.99:11485/v1`, model id `mellum`); `--profile DIR` for
another host. It runs the page's own before and after lines, checks port
8000 is free, and closes stdin. Record a kept check under
`evals/<date>-<slug>-check/` with `trace.jsonl`, `stdout.txt` and
`diff.patch` stripped; set the page's "Lesson check:" line to "held on DATE:
FAIL → PASS" and its Validation badge to `reference-run`.

## Try lessons in Pi

Copy the LAN profile to a scratch dir (Pi writes sessions into it), then:

```bash
PI_SKIP_VERSION_CHECK=1 PATH="$PWD/.baseline/pi-1.3.0/bin:$PWD/.baseline/node-v22.19.0/bin:$PATH" PI_CODING_AGENT_DIR=<scratch profile> pi --provider lan --model mellum
```

`/lesson E1` opens a lesson; `r` runs a line, `p` opens it as a project to
try by hand, `/lesson back` returns, `/lesson clear` starts a project over.

## Do not

- Change the LAN vLLM host — it is not ours, and E1's condition depends on it.
- Commit or print the vast.ai token (`~/.tokens/vast.ai`); renting needs the
  user's approval.
- Commit raw `trace.jsonl` / `stdout.txt` / `diff.patch`.
- Code to the eval, or put the framework name in commits or docs.

Known flake: the "kill ends every process with the server's name" node test
fails intermittently; CI has failed since before this work.
