# Rethinking the lessons: start from a failure that a condition produces

**What is measured.** Nothing new. This note draws on the 2026-10-29 screens
and checks: E4 and E1 on the 6-bit LAN host, the pinned BF16 host, and the
serving finding ([note](2026-10-29-lan-reasoning-leak.md)), plus the ladder's
rung designs ([rungs 10–12](2026-10-21-rungs-10-12-explained.md)).

**What is conjecture.** That a track built from pathologies a stated
condition produces will show FAIL → PASS in one session per arm, where the
current track did not. Each candidate below is a lead until its own before
arm fails on a screen.

## Why the current track is hard to prove

The lessons were written from failures seen in long suite runs (Bronze,
Silver, Gold: many phases, a growing context, 20–45 minutes), and each was
then given a small, clean challenge built from scratch. In a small clean
task the model does the competent thing:

- **E4 Running Commands:** the foreground-server stall showed in 4 of 9 bare
  BF16 sessions on the suites. On its own challenge, with clean serving, the
  6-bit backgrounded its own servers (1 stall in 4 clean before sessions).
- **E1 Looking Around:** the 245-call `ls -R` loop came from a run whose
  tool outputs were huge SVG dumps. On two challenge versions the 6-bit
  searched with `grep` and `awk` and never repeated a call.

Three things compounded it: these failures are odds, not certainties (a
1-in-3 failure rarely shows in one session); one setup raised the odds
(reasoning fed back as text tripled the stall rate, 3 of 4 against 1 of 4);
and our own harness faults voided runs. The lesson contract asks for a FAIL
a learner sees on `r`, every time. Luck-dependent pathologies cannot meet it.

## The principle

**A lesson's pathology must be produced on demand by a condition the lesson
states.** The before line sets up the condition; the failure follows; one
remedy removes it under the same condition. The order of work changes with
it:

1. Name the condition and the failure, with the record that showed it.
2. **Screen first:** one bare session under the condition. Only a pathology
   whose before arm fails on the screen becomes a lesson.
3. Then the challenge's polish, the preregistered check, the page.

The FAIL may be read from the record, not only from hidden tests: a failure
of serving or of the session (reasoning returned as text, an overflowed
context, a hung call) is real even when the files look fine. The harness
grades those from the trace into `run.json`, and the tutor's FAIL screen
names them the same way it names a missed check.

## Candidates, by where the failure lives

Each row is a lead until its screen fails. "Seen" points at the record.

**Easy: the plumbing.** Failures of serving and context, set up by a
setting. Fast, deterministic, and every learner meets them first.

| Pathology | Condition | Seen | Remedy |
| --- | --- | --- | --- |
| Reasoning returned as text | A serving stack whose template or reasoning parser misses streamed follow-ups | LAN host, 236 of 244 turns | `mellum-think-tags` adapter, as a unit (built) |
| Context overflow from a tool | A tool output bigger than the window (a 500,000-row file, rung 12) | Rung 12; finals ending on overflow in the nudge lesson's runs | A unit that trims oversized tool output (to build) |
| Thinking spends the output cap | A small `max_tokens` | One-turn smoke at 32 tokens: empty content | A unit or profile setting that reserves answer budget (to decide) |
| Runaway turns | A task with a requirement that cannot be met | Pi has no turn cap | `guard/cap-turns` (built) |

**Medium: the task traps.** Conditions inside the task: what the model
cannot know or is led to misread.

| Pathology | Condition | Seen | Remedy |
| --- | --- | --- | --- |
| Guesses an API it never saw | A library past the model's training cutoff | The 307 redirect loop; Python 3.15 on the ladder | `tool/lookup-library-docs` (built) |
| Takes the decoy | A helpful-looking helper that does the wrong thing (rung 10) | Rung 10's design and runs | `context/add-project-facts` naming the rule (built) |
| Reads the obvious rule, not the real one | A trap row whose meaning differs from its status (rung 11) | Rung 11's design and runs | the same, or a check (to decide) |
| Guesses the test command | A project whose tests run only through its own command | M1's three facts-off sessions | `context/add-project-facts` (built) |
| Finishes with lint errors | A task that invites unused imports, graded with lint | Suite runs graded with `--grade` | `check/check-code-quality` (built) |

**Hard: orchestration.** Conditions of length and phases, remedied by a
driver, not a unit.

| Pathology | Condition | Seen | Remedy |
| --- | --- | --- | --- |
| Breaks an earlier phase | A multi-phase build in one session | Silver and Gold runs | `workflow/spec-driven-flow` |
| Trusts its own incomplete test | A phase whose natural test misses a requirement | The Phase 4 id miss | the frozen acceptance test (`--flow-mode free`) |
| One attempt fails by chance | A task with a low pass rate per attempt | Gold runs | best of N (`--retry-concurrency`) |
| You build the tool, you build the remedy | Either of the above, with the learner's file | | the learner's file, with a reference |

## What happens to the pathologies that need luck

The foreground-server stall, the repeat loop, the machine-wide search and
the whole-file rewrite are real and recorded, and their guards stay in the
remedies list for The Challenge, where long runs meet them. They become
lessons only if a condition is found that produces them on demand, and the
screen shows it. The pathologies page keeps them as they are.

## What would falsify this

Screens of these candidates' before arms that pass, as E4 and E1 did. Then
"a condition produces it" was wrong for that pathology, and it drops out
the same way.

## Risks

- Easy becomes partly about serving and the harness, not the model. That is
  honest: from outside the two look the same, and a learner on a real host
  meets the plumbing first.
- Some conditions are contrived (a 500,000-row file). Each page has to say
  what its condition stands for in real work.
- Rungs 10 and 11 were built for the ladder's mediated worker; whether the
  6-bit fails them bare in Pi is exactly what the screen decides.
