# Applying the preserved rules to Satyrn Pi

This document records the 2026-11-16 scope decisions approved by the requests to
apply the design review and ground the port in Superpowers/SDD. Read it with [BRIEF.md](../BRIEF.md), then the
verbatim [SDD process](sdd.md) and [source project rules](provenance/mellum-worker-AGENTS.md).
Phase 2 creates the new repository's root `AGENTS.md` as an index to these
effective rules and re-earns the checks. The preserved files remain unchanged.

## Precedence and scope

Explicit user instructions take precedence. Within this handoff, the fixed
decisions in BRIEF.md and the mappings below govern conflicts with the preserved
source documents. All other source process rules remain in force. A copied
historical claim retains its original model, host, grader and evidence scope;
copying it does not measure Satyrn Pi.

| Source wording or path | Effective meaning in Satyrn Pi |
| --- | --- |
| Superpowers cycle and its roadmap conventions | Contributor development uses Superpowers skills throughout the port and ongoing work. SDD adds phase/cycle rows, caps, evidence rules, plan lifecycle and close checks. Phase 2 records the skill revision/setup and proves it works for a new contributor; it does not defer the workflow until then. |
| A phase is a container; a cycle delivers one lesson | A phase contains feature cycles. Each cycle ships one bounded user-visible behaviour or explicitly named infrastructure. Lessons, the learning centre, challenge and gamification remain with Education. |
| Pi and OpenCode; prohibition on npm lifecycle scripts because of pacote | Pi only. No OpenCode code, install lines, tests or install-path compatibility rules enter the active product. This removes that particular script prohibition; it does not require adding any lifecycle script. |
| `learn/glossary.md` | `docs/glossary.md`, using the same `###` entries and automatic first-occurrence linking when the Zensical site lands in phase 3. |
| `learn/pathologies.md` | `docs/pathologies.md`, a record of observed worker failure shapes with evidence, not an Education lesson. Add an entry only when a cycle observes a new shape. |
| `ladder/` and its old commands | The new eval package and `uvx satyrn-pi eval`. Phase 5 documents the source-checkout invocation; phase 6 supplies the preserved suites. Old commands remain provenance, not instructions to transplant the ladder. |
| `evals/`, stripped records and research release assets | Same evidence policy. New runs start in ignored `runs/`; keep selected `run.json` records and scores under `evals/`, with raw evidence in release assets. |
| `npm test` and the Python ladder tests | Phase 1 establishes the new default Node and Python test commands. Both use no model, network or subprocess; a separate integration tier exercises process behaviour outside default CI. Python always runs through `uv run`. |
| Tests for caps, lifecycle and evidence wording | Preserve the contracts and re-earn the tests in phase 2. The copied prose is not proof that a gate already exists. |
| Tags matching one package and two README install lines | One release tag agrees with both published package versions, the active Pi/npm and uvx install instructions, and CHANGELOG.md. No OpenCode install line. |
| `## Mellum`, `MELLUM_MODE`, `/mellum` and other old interfaces | Reference behaviours, not permission to bundle remedies. Phase 8 specifies the new command and mode interfaces, including model restoration and history integrity; compatibility names are a cycle decision. |

Caps, test-first discipline, screen/preregistration distinctions, one remedy per
cycle, agnosticism, changelog exemptions for internal SDD records, dated
corrections, immutable archived plans and the close checklist all still apply.
Runtime architecture follows BRIEF.md: the thin worker bundles no prompt,
guard, project facts or tool narrowing. Preserving prompt text does not make
it an active remedy or exempt a future fragment from the agnosticism rule.

## Phase 2 acceptance

Check both preserved files against source commit `0e4a9b68`. Publish the root
rules index and every mapped destination needed by the close checklist,
including the glossary and pathology record. Prove the document-cap and
lifecycle gates, the default-test tripwire and package import direction with
tests shown to fail first. If the backlog is empty, the checker accepts it;
it must not require inventing deferred work to satisfy a minimum-entry test.

Record the Superpowers revision, how contributors make its skills available
to Pi, and how an agent discovers the root rules index. Demonstrate the path
from an approved cycle description through any needed spec/plan, execution,
review, fresh verification and close records. That may use this infrastructure
cycle's own artifacts; do not invent a product feature just to prove process.
Keep Superpowers as the skills framework and these documents as repository
policy; a local wrapper skill may point to them without duplicating them.

Before phase 2 closes, its closing checklist must resolve every active path
and execute both default suites. Later phases add site presentation and
runtime implementations; neither is claimed by this document.

These requirements continue after the port. Any supplemental upstream adoption
is a named decision with a revision, affected contracts and evidence limits;
fetching newer code does not replace the original provenance or bypass SDD.
