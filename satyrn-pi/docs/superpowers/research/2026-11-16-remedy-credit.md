# Remedy credit on the rewritten stack

## What is measured / what is conjecture

**What is measured:** the source's Easy ladder records incremental screens,
including n=6 runs. No Satyrn Pi remedy has been implemented or measured here.
**What is conjecture:** which remedies will help on each suite on the rewritten stack.

## Source evidence and deliberate departure

The [source Easy ladder](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/docs/superpowers/research/2026-11-02-easy-ladder.md#L25)
records 4/6 for two prompt units, 5/6 after adding the foreground-server guard,
and 6/6 after adding the verify prompt. The source calls these leads; these
counts do not establish comparative rates, and a guard not firing in one cell
does not establish that it has no effect in other conditions.

Andre's [reply explicitly refuses empty presets](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/docs/superpowers/research/2026-11-13-reply-to-handover.md#L98)
for the source repository and requires a ladder run to re-derive its measured
settings. Satyrn Pi deliberately starts its remedy presets empty because its
implementation and tests are re-earned. That new-repository choice does not
invalidate the source records or mean no run credited the units.

## Owners and promotion procedure

Phases 10–12 own the Easy, Medium and Hard choices. Andre/Paul implement one
candidate per cycle; Nicola approves promotion; Ben documents the resulting
user interface and evidence limits. Follow the copied SDD measurement rules.

The [November 15 upstream screen](2026-11-16-upstream-acceptance-feedback.md)
adds a lead for a Medium acceptance-redispatch candidate: tell the worker
both the expected behaviour and the observed failure. Only one rep actually
received corrective feedback. It neither selects that candidate in advance
nor earns a preset addition here. If chosen, declare the gate-message version
alongside the grade and keep the generic delivery mechanism agnostic; fixture
expectations remain in suite-owned tests, not generic worker/remedy code.

**Terminology correction, 2026-11-16:** the earlier handoff called the thin
worker "baseline worker". The public progression is now Vanilla → Base →
Easy → Medium → Hard. Base begins with an empty common remedy list; later
stages retain their predecessors' units explicitly. Retaining units does not
earn a claim that they help a different suite.

**Vocabulary clarification, 2026-11-16:** "stages" above needs no separate
product concept. Refer to the names directly; each preset lists all its
remedies. Vanilla loads no remedy preset. See the
[vocabulary review](2026-11-16-vocabulary-review.md).

1. Retrieve the suite's failure evidence and declare the exact comparison.
   Vanilla is Pi plus recorder; Base is the thin command/mode extension plus
   its explicit common preset, initially empty. Record all selected units.
   The old `baseline-worker` preset is a historical bundle, not the new Base.
2. Screen an agnostic candidate, reading what the model received, did and was
   scored on. Name its pathology and record the screen's n and limitations.
3. Before any deciding run, preregister arms, n, grade version, cost reading,
   host/run settings and the decision rule. The suite's target and promotion
   threshold belong in that preregistration, before seeing deciding results.
4. Compare the candidate addition against the declared current remedies, with all
   previously selected units listed. Record oracle and composite outcomes and
   rejected candidates. A screen alone does not populate a preset.
5. Promote only under the fixed rule, linking the kept `evals/` records and
   reviewed raw release assets. Declare whether the addition belongs in Base
   or the target preset; update cumulative lists and requalify affected presets
   before new claims. Otherwise keep it opt-in or reject it; write the verdict
   without inventing a pass.

The full source prompt crosses verbatim as provenance. That does not install
it by default or authorise a monolithic swap or suite-specific answer in a
new remedy. Active fragments must satisfy the brief's agnosticism contract.
Unit metadata saying "unmeasured" is not a substitute for retrieving records.

## What would falsify this

A deciding run that fails its preregistered rule falsifies promotion for that
candidate and suite. A different baseline, changed grade or leaked suite answer
invalidates the proposed attribution and must be recorded before rerunning.

## Risks

Small screens are noisy; addition order can affect credit. Host changes,
context-file policy, tool availability and grader revisions can confound a
comparison. No suite is promised a passing preset before it is measured.
