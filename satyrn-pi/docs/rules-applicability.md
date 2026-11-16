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
| Baseline Worker, `bare`, `arm` and `rung` | Use Vanilla → Base → Easy → Medium → Hard directly. Base is the thin worker plus its explicit common preset, initially empty. An arm is a research comparison variant; `bare` and rung IDs belong in source mappings and historical citations. See the [vocabulary review](superpowers/research/2026-11-16-vocabulary-review.md). Historical names and records are not rewritten. |
| `learn/pathologies.md` | `docs/pathologies.md`, a record of observed worker failure shapes with evidence, not an Education lesson. Add an entry only when a cycle observes a new shape. |
| `ladder/` and its old commands | The new eval package and `uvx satyrn-pi eval`. Phase 5 documents the source-checkout invocation; phase 6 supplies the preserved suites. Old commands remain provenance, not instructions to transplant the ladder. |
| `evals/`, stripped records and research release assets | Same evidence policy. New runs start in ignored `runs/`; keep selected `run.json` records and scores under `evals/`, with raw evidence in release assets. |
| `npm test` and the Python ladder tests | Phase 1 establishes the new default Node and Python test commands. Both use no model, network or subprocess; separate integration tests exercise process behaviour outside default CI. Python always runs through `uv run`. |
| Tests for caps, lifecycle and evidence wording | Preserve the contracts and re-earn the tests in phase 2. The copied prose is not proof that a gate already exists. |
| Tags matching one package and two README install lines | One release tag agrees with both published package versions, the active Pi/npm and uvx install instructions, and CHANGELOG.md. No OpenCode install line. |
| `## Mellum`, `MELLUM_MODE`, `/mellum` and other old interfaces | Reference behaviours, not permission to bundle remedies. Phase 8 specifies the new command and mode interfaces, including model restoration and history integrity; compatibility names are a cycle decision. |

Caps, test-first discipline, screen/preregistration distinctions, one remedy per
cycle, agnosticism, changelog exemptions for internal SDD records, dated
corrections, immutable archived plans and the close checklist all still apply.
Runtime architecture follows BRIEF.md: the thin worker bundles no prompt,
guard, project facts or tool narrowing. Preserving prompt text does not make
it an active remedy or exempt a future fragment from the agnosticism rule.

## Roadmap workflow

Read [BRIEF.md](../BRIEF.md), this document and the preserved [SDD process](sdd.md)
before editing the roadmap, a spec or a plan. Superpowers supplies the contributor
skills; SDD adds the roadmap rows, caps, evidence rules, plan lifecycle and close
checks. Use them from P1.1; phase 2 proves a reproducible contributor setup. The
subject worker loads none of these contributor skills by default.

A phase is a container, not a single cycle. Initial rows describe proposed
outcomes, not approved specs or complete plans. At each phase's opening
brainstorm, retrieve existing decisions and evidence, then split or add bounded
cycles as needed before implementation. Each cycle follows brainstorm → spec
when behaviour changes → plan when needed → execute → review/close, with human
approval before implementation. Keep phase order and settled decisions; name
any proposal to reopen one. Andre and Paul implement, Nicola approves PRs, and
Ben owns docs and onboarding. Each cycle includes its documentation.

For remedies, add one candidate per cycle after reading the preceding evidence.
Screens explore; preregistered runs decide promotion. A rejected candidate
closes with its evidence and no preset addition. Vanilla loads no preset;
cumulative flat presets still require qualification on their target suites.

Close cycles with the [mapped checklist](sdd.md#closing-a-feature-cycle), fresh
verification, Nicola's PR approval and plan close/archive records when a plan
exists. Keep closed rows; move deferred work to the backlog with reopen
conditions. A phase closes with a reviewed outcome, including a negative one;
closure does not publish packages or claim a pass rate. Define release checks
for both packages before publishing.

This workflow continues after phase 12: add cycles to the relevant phase or a
new phase for new work. Changes to contributor tools get a bounded infrastructure
cycle. The roadmap remains the current work index.

## Phase 2 acceptance

Check both preserved files against source commit `0e4a9b68`. Publish the root
rules index and every mapped destination needed by the close checklist,
including the glossary and pathology record. Prove the document-cap and
lifecycle gates, the default-test tripwire and package import direction with
tests shown to fail first. If the backlog is empty, the checker accepts it;
it must not require inventing deferred work to satisfy a minimum-entry test.

Use P1.2's domain description, vocabulary inventory and agreed numeric budget
to implement the jargon check. Check the declared learner-facing scope and
aliases, allowing historical citations and ordinary uses of words. The check
does not replace review of whether terms preserve the intended meaning.

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

## Documentation site acceptance

P1.1 locks `zensical` and `zensical-glossary` as development dependencies in the
same uv environment. P3.1 configures and verifies the site. Adapt the theme from
[`satyrn-ai/satyrn-website`](https://github.com/satyrn-ai/satyrn-website/tree/7508bd78e17d0428348481db40d8664beee9e60d):
its `zensical.toml`, `src/stylesheets/satyrn.css` and relevant `overrides/` define
the Satyrn colours, typography, light/dark appearance and site chrome. Record the
revision and assets actually adopted; resolve font availability when selecting
assets. A separate shared theme package is not assumed. Keep sources plain
Markdown; website blog and landing-page features are outside this cycle.

Follow the source repo's verified glossary setup: configure
`project.markdown_extensions.zensical_glossary` with `glossary_file` resolving to
`docs/glossary.md`, `heading_level = 3`, `first_only = true`, and a `base_url`
matching the deployed site path. Review aliases against the vocabulary
decisions; do not hand-link prose terms or preserve misleading aliases.

Set up GitHub Actions to run `uv sync` and `uv run zensical build --strict`
on pull requests, then build and deploy the website to GitHub Pages from main.
Configure Pages, record its public URL, and verify the deployed site; align
`site_url` and glossary links with the actual base path. Use
`uv run zensical serve` for local preview. Confirm first-occurrence links, alias
targets and exclusions for code, headings and existing links in rendered pages.
Check theme assets and glossary links in light/dark mode and under the deployed
base path. These site checks are separate from the model-free default tests.
