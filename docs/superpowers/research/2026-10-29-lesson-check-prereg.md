# Preregistration: does each lesson fail without its remediation?

**What is measured.** Nothing yet: this fixes the arms, n, scoring and rule
before the run, on 2026-10-29, at commit `4ba233c`.

**What is conjecture.** That each lesson's remediation is what separates its
two arms. Three pages already report a null (E3, E4, M3) and one reports
0/3 in both arms (M4); for those the rule below is expected to read "does
not hold", and that is a finding about the page, not a failed run.

## The question

The standard for a lesson: without its remediation the lesson's suite should
fail, and with it, it should do better. Each page's "Run it yourself" block
already names both arms.

## Setup

`scripts/baseline/baseline.py lessons --full` on the pinned vLLM host (RTX
A6000, Mellum 2.1 BF16, vLLM 0.32.0, Pi 1.3.0): each page's commands at the
page's own n and deadline, the 120 s stall cutoff, three sessions at a time.
The host is shared with a running flow job.

| Lesson | Suite | Remediation arm (R) | Without arm (W) | n per arm |
| --- | --- | --- | --- | --- |
| E1 | easy, medium, hard | `worker` | `bare` | 3 |
| E3 | easy | `worker` | `no-facts` | 3 |
| E4 | easy | `worker` | `no-prompt` | 3 |
| M1 | easy, medium | `worker` | `strip-thinking` | 3 |
| M2 | easy | `worker` | `no-nudge` | 5 |
| M3 | medium | `worker --specs split` | `worker --specs joined` | 3 |
| M4 | medium | stepped (`--specs joined`) | `--single-prompt` | 3 |
| H1 | easy, medium | `worker` | `bare` | 3 |

E2's remediation is a harness check with no "without" arm, and H2 has no
command; neither can be tested by this rule and both are reported as such.

## Scoring and rule

A session passes when every hidden check passes (`--grade`). Per lesson and
suite, count passing sessions in R and W.

- **Holds:** W passes no session and R passes at least one.
- **Direction only:** R passes more sessions than W, but W passes some.
- **Does not hold:** R passes no more sessions than W.

A tie at 0/n in both arms "does not hold": the suite is too hard to show the
remediation at this n. Secondary, reported but not deciding: hidden checks
passed per session, and the failure each page names (M2's out-of-layout
writes, M4's `checks_ran`, M1's output tokens).

This is a screen at n = 3 (5 for M2): a "holds" is a lead for the page, not
a rate, and a "does not hold" on a page that claims a separation means the
page must say so.

## What would falsify this

A lesson whose W arm passes as often as its R arm across this run and the
page's own record: its remediation is not what the page says it is.

## Risks

- Shared host: a flow job runs alongside; wall and token numbers are not
  comparable with the pages', passes are.
- n = 3 cannot separate a small effect; a "does not hold" is not proof of no
  effect.
