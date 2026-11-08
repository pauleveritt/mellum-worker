# `prompt/verify-the-spec` on Easy, and what Easy can tell us

## For Andre

- **What this is:** a screen (n = 3 per arm), run after R.1 closed. It asks whether the one cheap
  unit aimed at Easy's real failure moves it. R.1 had ruled the unit out as a candidate.
- **Result, a lead:** no. The line reached every request, and the model still missed the title
  override in 3 of 3 sessions. We don't plan a counted batch for it on this evidence.
- **What to look at:** the per-check table below. Easy's misses sit on two checks, so a mean or a
  full-pass count says little about what a unit did.

**What is measured.** Six counted Easy sessions on 2026-11-08
([record](../../../evals/2026-11-08-r1-verify-screen/table.md)), and per-check misses recomputed
from R.1's committed records (step one, two and three).

**What is conjecture.** That a prose reminder cannot fix this failure at any n; why the model defers
the title block; that Medium and Hard will spread remedies better than Easy does.

## Ladder run

Harness, Easy (13 checks), M5 Max, llama.cpp b12110, Pi 1.4.0, thinking on, `--host-card`, budget
proxy, `scripts/r1_batch.py`. Arms: `--arm vanilla` and `--arm vanilla --remedy
prompt/verify-the-spec`, interleaved.

| Check | Vanilla (of 3) | verify-the-spec (of 3) |
|---|---|---|
| Title override | 3 | 3 |
| Launch with reload | 2 | 0 |

Vanilla missed the launch check in 17 of 48 counted R.1 sessions, so 0 of 3 is unremarkable. A
unit as strong on the title as the mediated test (5 and 6 misses, of 24 and 23) would rarely miss
3 of 3. A weak one could.

**Where Easy's misses are** (counted R.1 sessions, checks that ran):

| Arm | Sessions | Title override missed | Launch check missed |
|---|---|---|---|
| Vanilla, three steps | 48 | 46 | 17 |
| bounded, overnight | 24 | 19 | 4 |
| fg-server, overnight | 24 | 20 | 12 |
| mediated+bounded, overnight | 24 | 5 | 3 |
| mediated+fg-server, overnight | 23 | 6 | 5 |

## What this means for reading Easy

- Easy separates remedies poorly: a unit either moves these two checks or barely registers on
  quality. An empty `preset:easy` means nothing cheap fixed them, not that the units have no value.
  `bounded` did what it is for, no stalls within budget; R.1's rule did not judge that.
- A unit's general value needs Medium and Hard, which have no counted Vanilla floor on the repaired
  oracle yet.
- From now on, preregister each unit on the failure it claims to fix, with quality and budget as
  guards against harm, and report misses per check (`r1_batch report` now does).

## Persuasion → enforcement

`verify-the-spec` is persuasion, on `before_provider_request`: a line on every user message. It
landed, in the sense that the model got it every time, and did not change what the model built. In
r03 the model named the requirement and deferred it. The mediated test is what moved this check
(22 misses to 5 and 6): it runs at `agent_before_settle` and sends the failure back. That fits the
standing rule to prefer a guarantee over a sentence. The open work is making that guarantee cheaper.

## What would falsify this

- A counted batch where `verify-the-spec` cuts title misses by a third or more against Vanilla.
- A Medium or Hard floor with misses as concentrated as Easy's: then Easy is not the odd one.

## Risks

- n = 3. Three misses rule out a strong effect, not a modest one.
- The unit appends to every request as written; a once-per-task delivery was not tried.
- Two of six sessions were dominated by unrelated collapses (a stall at 13 failed; no templates).
