# Does each lesson fail without its remedy? The result

**What is measured.** The preregistered lesson check of 2026-10-29
([prereg](2026-10-29-lesson-check-prereg.md),
[record](../../ladder/2026-10-29-lesson-check/README.md)): every lesson's
arms at the page's n on the vLLM host, valid sessions only (seven arms voided
by a tunnel drop were rerun). Lesson numbers below are the preregistered
ones.

**What is conjecture.** Why each lesson fails the rule; any rate (n = 3, 5
for M2). That a lesson challenge of its own would separate the arms where the
suites do not.

## The rule

Holds: the without arm (W) passes no session and the remedy arm (R) passes
at least one. Direction only: R passes more than W but W passes some. Does
not hold: R passes no more than W.

## Result

| Lesson (prereg) | Suite | R | W | Verdict |
| --- | --- | --- | --- | --- |
| E1 Baseline | easy / medium / hard | worker 3/3, 0/3, 0/3 | bare 2/3, 1/3, 0/3 | does not hold (3/9 each) |
| E2 Write only listed | easy | worker 3/3 | (no arm) | not testable |
| E3 Project facts | easy | worker 3/3 | no-facts 2/3 | direction only |
| E4 Short prompt | easy | worker 3/3 | no-prompt 1/3 | direction only |
| M1 Thinking | easy / medium | worker 2/3, 1/3 | strip-thinking 3/3, 3/3 | does not hold (reversed) |
| M2 Guards for empty turns | easy (n = 5) | worker 4/5 | no-nudge 5/5 | does not hold (reversed) |
| M3 One spec per phase | medium | split 1/3 | joined 1/3 | does not hold (tie) |
| M4 Prose brief | medium | stepped 0/3 | single-prompt 0/3 | does not hold (both 0) |
| H1 Primary agent | easy / medium | worker 3/3, 2/3 | bare 2/3, 2/3 | direction only on easy; tie on medium |
| H2 Intercom block | n/a | n/a | n/a | not testable (no command) |

**No lesson holds.** Two show direction only (E3, E4), and H1 does on Bronze.
Three reverse: the arm without the remedy passed more (E1 on Silver, M1 on
both suites, M2).

## Reading

On this host, at full precision, bare Pi is strong enough to pass Bronze
two times in three, so a suite that bare Pi passes cannot show a remedy
turning FAIL into PASS. That is the measured case for the decision taken the
same day: each lesson gets a challenge of its own, built to provoke its one
failure (LC.26), and a lesson's check is run on that challenge, not on the
suites.

Two results stand apart from the floor problem and need their own look:

- **M1 (now M4), thinking:** stripping earlier reasoning passed 6 of 6
  against 3 of 6 kept, on both suites, the opposite of the page's ladder
  result (A12: stripping was 60% slower on oMLX). The page must say so; the
  ladder result was on another backend with a prefix cache this host may not
  share.
- **M2 (now M3), the nudge:** 5/5 without it against 4/5 with it. The nudge
  fires rarely on this host; the page's own record already calls it a null.

## Decision

Pages that claim a separation are corrected to this result; none says FAIL →
PASS until its own lesson challenge shows it. Lesson challenges are built in
the order the track needs them, starting with E5 (the foreground server,
which stalled four of nine bare sessions on this host).

## What would falsify this

A lesson challenge on which the without arm passes as often as the remedy
arm: then the remedy, not the suite, is the problem.

## Risks

- n = 3 (5 for M2) per arm and suite: one session moves a verdict.
- Shared host: the flow rerun ran alongside; passes are comparable, wall and
  tokens are not.
- The first run's tunnel drop voided seven arms; the rerun used a newer
  commit whose changes are behaviour-identical for these arms.
