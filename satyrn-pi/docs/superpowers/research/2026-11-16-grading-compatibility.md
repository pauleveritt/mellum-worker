# Grading compatibility and qualification

## What is measured / what is conjecture

**What is measured:** source inspection at `0e4a9b68` and retrieval of its
recorded reply, plus the [November 15 acceptance-feedback supplement](2026-11-16-upstream-acceptance-feedback.md)
retrieved on 2026-11-16. No new grader qualification or model run has been performed.
**What is conjecture:** that fresh grader implementations match the preserved
expectations and distinguish all relevant correct and defective builds.

## Fixed boundary

Copy suite fixtures, expectations and original run records verbatim. Re-earn
grader implementation and tests. The inherited grade remains the primary
reported number; Easy's [expected.json](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/learn/code/suites/easy/expected.json#L1)
lists four expected checks. Preserve the inherited expected IDs and semantics
for Medium and Hard too; their fixture content determines the contract.

A stricter Easy grade or a corrected Medium grade may run alongside the
inherited grade under a separate name and version. Neither replaces an old
record's grade. This follows the source reply's [metrics rule](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/docs/superpowers/research/2026-11-13-reply-to-handover.md#L16)
and [grader verdicts](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/docs/superpowers/research/2026-11-13-reply-to-handover.md#L68).
The initial brief left replacement of the primary grade open; this correction
closes that ambiguity for these twelve phases.

## Owner and phase-6 acceptance

Andre/Paul specify and implement the grading boundary in phase 6; Nicola
approves the contract and Ben reviews how score labels are explained.

- Inventory suites, fixtures, grader expectations and their source hashes;
  map each inherited grade to the corresponding immutable inputs.
- Treat acceptance-gate feedback as a separate versioned contract from hidden
  grading. Re-earn the expected/observed diagnostics from `3e20e161`, retaining
  the original gate revision as provenance and checking verdicts independently.
  Rebuild the wrong-favicon and route-only-ID witnesses, the complete-build
  success case and their message checks; no source test implementation is
  transplanted. Record the actual message delivered by a gate, including any
  truncation, when an active gate remedy is later measured.
- Show rewritten graders passing the known-good fixtures and rejecting the
  named known-broken fixtures. Verify expected test IDs actually execute;
  zero collection, missing IDs or skips cannot become a pass.
- Add witness cases for known grading gaps, recording which the inherited
  grade accepts or rejects. A known limitation stays visible; correcting its
  semantics requires a distinct grade version.
- Record grade identity, suite identity, oracle verdict and any composite
  quality verdict separately. Qualify against worker-controlled pytest config
  and record any difference from the source execution path. A changed grading
  environment is not assumed comparable solely because assertions match.
- Define metric fields before publishing new scores. The source [sets turns
  equal to requests](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/learn/code/harness.py#L996);
  its reply [acknowledges the issue](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/docs/superpowers/research/2026-11-13-reply-to-handover.md#L76).
  Imported records retain that historical meaning. New accurate fields get
  explicit definitions and are not compared as though the old field meant them.

Qualification checks require no subject-model run. Process execution belongs
in marked integration tests; contract and fixture checks use the default
tests where possible. Do not claim a grade version is qualified until its
qualification evidence exists.

## What would falsify this

A mismatch in preserved fixture/expectation hashes falsifies a verbatim-copy
claim. A rewritten inherited grader disagreeing with a source witness build
requires diagnosis before claiming compatibility. A failure shape the grader
cannot distinguish limits the claims made from its pass count.

## Risks

The inherited grade is known to be lenient. Preserving its label protects
historical meaning; it does not establish complete acceptance coverage.
Different grader environments may change outcomes despite unchanged assertions.
