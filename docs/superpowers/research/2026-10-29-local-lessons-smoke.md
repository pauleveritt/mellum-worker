# Local 6-bit runs the lessons — an n=1 smoke of every harness command

Date: 2026-10-29. Lifecycle: screen (n = 1 per command, one serving stack, one
host). The point was to check that the local 6-bit path drives every lesson's
own harness command and reaches a grade — the companion to the ladder baseline
(`docs/superpowers/research/2026-10-29-local-mellum-baseline.md`). The record is
`evals/2026-10-29-local-lessons-smoke/`.

## What is measured / What is conjecture

**Measured.** Each lesson's "Run it yourself" command, run once against Mellum
2.1 6-bit on oMLX 0.7.1rc1 (Apple M3 Max), vanilla Pi 1.3.0, through the shipped
`learn/code/harness.py`, deadline capped at 900 s, graded. 43 command rows; 4
lessons ship no harness block, 2 are template placeholders, 1 is a `--dry-run`,
leaving **36 real graded runs — 32 PASS**.

| Tier | Graded | Pass |
|------|-------:|-----:|
| Easy | 11 | 11 |
| Hard | 6 | 6 |
| Medium | 19 | 15 |

The four failures are two lessons. **M1 build-a-harness** runs the AgentClinic
suite `--arm bare` (no remedies, no `--grade`) by design — the lesson's point is
to show what the provided harness and remedies add. Unguarded, the 6-bit model
tried to verify its work by starting a **foreground web server**: both easy runs
hit the 120 s stall cutoff on `uvicorn main:app …` (the second cycled ports
8000, 8001, 8002), and the medium run hit the 900 s-capped deadline (604 s, 129
requests, 39 tool errors) in a bare flail with no server. **M9 one-spec-per-phase**
`--specs joined` failed the complexipy code-quality grade while `--specs split`
passed the same seed. The run took 156 min end to end.

**Conjecture.** The local path is sound: the model drives the harness, loads
remedies, and grades green across every easy and hard lesson and all the
remedy-ladder mediums. The two failing lessons are the ones that strip the
guards or hand over the hardest input, not a capability gap. M1's stalls are the
textbook case for `tool/background-long-commands` — a foreground server blocks
the bash tool forever — and M6 run-long-commands-safely, which applies that
remedy, passes; the lesson is demonstrating exactly why the harness and its
guards exist. M9's joined-spec variant failing where the split sibling passes on
the same seed points at input density, not capability. Neither is a new failure
mode; the known shapes reappear where they were expected.

## What would falsify this / Risks

- **n = 1 per command.** A smoke, a lead — not a rate. A FAIL here could flip to
  PASS on a re-run, and a PASS could be a lucky single sample. The pass count
  says "the path works and grades", not "it passes 89% of the time".
- **900 s cap, not the lessons' own budgets.** The M1 medium that hit the
  deadline might converge with the page's real n and deadline (the `full` run).
  This smoke caps deadline and forces repeat 1, so a deadline FAIL is "did not
  finish in 900 s", not "cannot finish".
- **One stack, one host, one quant.** oMLX/MLX on Apple silicon only. The grades
  carry the 6-bit quant cost measured in the ladder baseline (−5 vs BF16), so a
  FAIL here can be quant, harness, or the lesson's own difficulty — this run
  does not separate them.
- **Template and no-command rows are expected, not failures.** The 2 exit-1 rows
  are fill-in-the-blank commands (`path/to/your-remedy.ts`); counting them as
  failures would be wrong.

## Decision

Keep this as the local smoke: it confirms the 6-bit oMLX path runs the whole
lesson set and grades, and it localises the two failing lessons to a stripped
guard (M1, bare arm) and a dense input (M9, joined spec), not a capability gap.
It moves no measured default and opens no new lead — it is corroboration, cheap
to re-run on the laptop. If anything, M1's foreground-server stalls are a clean
demonstration that `tool/background-long-commands` earns its place: the bare
run stalls on `uvicorn`, the remedied M6 run does not.
