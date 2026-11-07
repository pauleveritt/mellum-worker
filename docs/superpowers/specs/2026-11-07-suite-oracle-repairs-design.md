# F.4 — Repair the suite oracles before R.1

## For Andre

The independent review of `integration` at `bc5db20` reproduced false wins,
a false loss, and workspace control over grading. Repair the instrument before
R.1; this is infrastructure, with no remedy or model-performance claim.
The [audit](../research/2026-11-07-suite-oracle-audit.md) preserves the evidence.
The [cycle procedure](../../sdd.md#branches-and-worktrees) requires a squash-merge
into `integration`, followed by worktree and branch cleanup.

## Scope and compatibility

Keep Vanilla plus the recorder and the thin worker unchanged. Preserve every
historical prompt/spec byte, including the materialized `original` variant.
Repair current suites against their written contracts, without adding an
unstated UI order, extra route policy, or new application requirements.
Cover all reported findings; the already-excluded qualify redesign, settle
behavior, port preflight, Pi-version recording and acceptance-package port stay out.
Easy still requests only Phase 1. Its current grader will cover the full existing
Phase 1 Acceptance list; this does not add later Easy phases to the task.

## Trusted grading boundary

The harness grades a disposable copy of the submitted application. Hidden tests
live in a separate trusted directory and never enter the model's workspace.
The grading interpreter/dependencies come from the selected suite's trusted base
configuration and lock, not the submitted pyproject, lock, virtualenv or plugins.
For suites without project metadata, use a minimal trusted pytest environment.
Hidden pytest uses trusted configuration, no workspace conftests or automatic
plugins, and a sanitized environment. Application modules remain importable;
local templates and SQLite files resolve inside the disposable application copy.
Structured per-test results determine outcomes; application stdout cannot forge
passed expected checks. Missing, skipped and uncollected required checks fail.
This prevents the demonstrated configuration bypass, not arbitrary hostile Python
from attacking its host; an operating-system sandbox is outside this cycle.

Run project tests separately, with their legitimate conftest support, under the
trusted dependencies. Required starter tests cannot disappear or be weakened;
added tests must pass. Preserve existing hidden-behavior and optional quality
outcomes separately in the record. Do not silently add layout to overall pass.
Report created, modified and deleted paths, and declare allowed helpers explicitly.

## Current suite contracts

Shared page checks verify direct HTTP status, HTML5 doctype semantics, visible
navigation and branding. Controls belong to their applicable usable form.
Each state operation changes its target only, preserves other records, exposes
the correct controls, and preserves the complete board order after each action.
IDs are integers, unique and increasing across seeds and subsequent additions.
Seed text is exact; displayed dates correspond to their complaint timestamps.
Each test starts from independent application/database state rather than relying
on test-module order. Reordered modules also remain a regression control.

Easy additionally checks template inheritance, viewport, Bootstrap assets and
placement, favicon, default/overridable title, hero/welcome, and the documented
uvicorn launcher with reload and its main guard. Launch probes use isolated
ports and bounded process groups with cleanup; they do not depend on port 8000.
Do not require arbitrary wording or a CSS class for a hero the spec does not name.

Hard checks archive rejection invariance, repeated rejection, redirect destination,
and exactly one correctly typed audit entry for every specified transition.
Migrations are exercised on a pristine database through the documented command;
check index definitions, exact view contents/type, nullable columns, permitted
backfill changes, unchanged other rows, and full schema/data invariance on rerun.
Reports must follow private variations of real database rows; exercise boundaries,
omitted optional parameters, sorting/limits and strict numeric response types.
Existing SQL binding/database-computation requirements get explicit Acceptance
wording and verification; the contradictory blanket row-change prohibition is fixed.

## Grader identity and historical evidence

Before changing assertions, retain immutable pre-repair (`bc5db20`) and pre-single-
source (`16cf9f9^`) grading bundles, with their expected checks and dependency inputs.
`--specs original` remains a brief selection only. An explicit `--grader` selection
chooses current or a retained historical bundle; the default is current.
New records include the grader identity/digest and separate project-test outcome.
Historical bundles execute their historical assertions under the new trusted runner;
legacy unsafe runner behavior is not reproduced. Historical score comparisons name
both the assertion bundle and execution policy. Old records remain unchanged;
records without identity are unknown, never silently relabeled as current.
No automatic rescore or merge of unlike grader revisions is part of this cycle.

## Ladder run

No model or ladder run is needed to establish deterministic oracle repairs.
For each regression, first show the current grader accepts the wrong build or
rejects the valid one; then fix it and rerun. Keep positive alternative builds,
all three known-good fixtures, per-check negative witnesses, order controls,
original-byte manifests, and generic harness tests. Run the full Python harness
suite, ladder tests, `npm test`, document caps and docs build before cycle close.
R.1 still needs its own preregistered interleaved model runs; old rates do not transfer.

## Persuasion → enforcement

No Pi hook or additional prompt rule is introduced. Trusted dependency/configuration
selection, isolated grading, independent test state, complete assertions and recorded
grader identity enforce these contracts after the worker exits. Generic harness
code contains no suite route, table, column, expected value or prescribed solution.
