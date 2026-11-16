# Supplemental upstream review: acceptance feedback, November 15

## What is measured / what is conjecture

**What is measured:** on 2026-11-16, `git fetch origin main` resolved main to
`41fa54d03097d81db029b1f4c6f46b8fe6eeb98c`. Inspecting
`git log --reverse 0e4a9b68..origin/main` and
`git diff 0e4a9b68..origin/main` found the two Andre commits below. The run
results are retrieved from Andre's published note; no model runs or witness
qualification were repeated for this porting update.
**What is conjecture:** that the feedback behaviour will improve the rewritten
worker's repair success or cost. No preset or default is promoted here.

## Retrieved changes

| Commit | Scope | Porting disposition |
| --- | --- | --- |
| [3e20e161](https://github.com/andrevanzuydam/mellum-worker/commit/3e20e161c22cc55ac0625f4e50db5da94001560b) | Medium acceptance failures explain what they wanted and what they found; two regression tests; changelog update. | Re-earn the feedback contract and witness tests in phase 6; leave runtime redispatch for a separately measured remedy cycle. |
| [41fa54d0](https://github.com/andrevanzuydam/mellum-worker/commit/41fa54d03097d81db029b1f4c6f46b8fe6eeb98c) | Records the n=3 Medium screen and its attribution limits. | Retrieve as research evidence when selecting a Medium remedy candidate. |

The implementation [names the wanted favicon href beside parsed links](https://github.com/andrevanzuydam/mellum-worker/blob/3e20e161c22cc55ac0625f4e50db5da94001560b/ladder/fixtures/acceptance/test_medium.py#L216)
and [labels the IDs from direct and route creation](https://github.com/andrevanzuydam/mellum-worker/blob/3e20e161c22cc55ac0625f4e50db5da94001560b/ladder/fixtures/acceptance/test_medium.py#L310).
The [regression cases](https://github.com/andrevanzuydam/mellum-worker/blob/3e20e161c22cc55ac0625f4e50db5da94001560b/ladder/tests/test_acceptance_messages.py#L113)
rebuild a wrong favicon and IDs assigned only by the route. Andre reports
they were red on the previous messages and that classification stayed the
same on 43 witness builds. This review inspected the diff; that qualification
claim is attributed to Andre, not independently established for Satyrn Pi.

## Reported screen and its limits

The [source screen](https://github.com/andrevanzuydam/mellum-worker/blob/41fa54d03097d81db029b1f4c6f46b8fe6eeb98c/docs/superpowers/research/2026-11-13-reply-to-handover.md#L364)
reports Medium on the same rig, n=3, with only messages changed:

| Rep | Hidden score | Requests | Wall | Gate repair rounds | Acceptance at exit |
| --- | --- | --- | --- | --- | --- |
| 1 | 18/18 | 25 | 231 s | 0 | 9/9 green |
| 2 | 18/18 | 54 | 682 s | 1 | 9/9 green |
| 3 | 18/18 | 46 | 413 s | 0 | 9/9 green |

Rep 2 reportedly moved automatic ID assignment onto the dataclass after one
round quoting the new expected/observed message. Reps 1 and 3 passed on their
first attempts and never received corrective feedback. Their low cost cannot
be attributed to the messages. This is a lead, not a comparative rate or a
proven cost saving. These commits add the narrative screen record; they do
not add per-run `run.json` files or raw traces to the tree.

## Integration boundary and owners

Keep `0e4a9b68` as the original provenance pin. These two commits are named
supplements, not a wholesale rebase. No worker, preset, subject-model pin,
hidden suite grader, source AGENTS.md or SDD-process change appears in this
delta. Preserve those original records and rules unchanged.

Phase 6's Andre/Paul implementer must qualify the original verdict contract
and the supplemental feedback contract independently, with success and defect
witnesses. Give the acceptance gate and its messages an identity distinct
from the hidden grade: a message change can change the model's next action
even when pass/fail expectations stay fixed. Preserve the source gate revisions
as provenance; re-earn active implementation and tests.

If selected in phase 11 or later, an acceptance-redispatch remedy uses the
qualified expected/observed diagnostics, records which messages reach the
worker, and earns promotion through its own preregistered run. The mechanism
for delivering a failure stays general; suite-specific expected values belong
to the suite-owned acceptance test. Neither phase 6 nor this note activates
redispatch by default or codes a fixture answer into a generic remedy.

Nicola reviews the adoption decision; Ben reviews how the two kinds of score
and the evidence limits are presented. Use the same Superpowers/SDD cycle for
this adoption and subsequent upstream reviews.

## What would falsify this

A differing classification on the re-earned witnesses would falsify claimed
verdict compatibility and require a separately identified gate contract.
A preregistered comparison that fails its promotion rule would reject the
candidate's claimed benefit. Unchanged oracle scores alone do not prove a
feedback change is behaviourally neutral.

## Risks

The repair attribution rests on one feedback-exposed rep. The published screen
is not raw evidence reproduced here. Feedback truncation, a new gate runner or
a different host may change what the subject sees. Keep those conditions in
the deciding run's recorded contract.
