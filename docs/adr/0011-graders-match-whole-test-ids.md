# 0011: Graders match whole test ids; a parametrized test passes only when every case does

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

The harness and `py_features.py` counted an expected test as passed when the text `PASSED <id>` appeared
anywhere in pytest's output. A parametrized test's ids carry a `[case]` suffix, so `test_x` read as passed when
only `test_x[case1]` passed; a test whose id is a prefix of another (`test_plain`, `test_plain_twofold`) could
pass on the other's line. Found while writing `suites/tools-train`: a wrong solution showed green.

## Decision

`learn/code/grading.py` reads whole result lines. An id listed with its case suffix matches that line exactly;
an id listed without one passes only if it has at least one case and every case passed. The harness and the
task checker both use it.

## Consequences

The main screens (Easy, Medium, Hard, Python eval) have no parametrized graders, so their past results stand.
Four converted Satyrn graders (cell-loop, guard-prefixes, run-record-gate, speed-probe) do: their earlier grades,
and pairs built from the `2026-11-24-mint-satyrn` runs, may be too lenient. Satyrn tasks are re-checked under the
fixed grader before teacher data from them is used.

## Evidence

`learn/code/tests/test_grading.py` (shown red first); commit de9167ce.
