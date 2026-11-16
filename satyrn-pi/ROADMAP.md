# Satyrn Pi roadmap

Read [BRIEF.md](BRIEF.md), [rule applicability](docs/rules-applicability.md)
and [docs/sdd.md](docs/sdd.md) before changing this file.

## Now

In flight: the staged design handoff; no product phase has shipped.
Parked: tier selection and rented-host qualification await their [research owners](BRIEF.md#decisions-the-research-documents-own).
Next: [P1.1](#phase-1--repository-and-dependencies), using the [Superpowers/SDD workflow](BRIEF.md#how-we-develop-superpowers-sdd-and-the-roadmap) to create the repository from this tree.

## How to read the rows

Phases run in the agreed order. Each row is a feature cycle, with its own
brainstorm, spec when behaviour changes, plan when needed, and review/close.
Rows below are proposed deliverables, not completed specs or implementation
plans. Andre and Paul implement; Nicola approves PRs; Ben owns documentation
and onboarding. Each cycle includes the documentation its deliverable needs.

Superpowers supplies the contributor skills. The preserved SDD process and
applicability rules extend them with these phase/cycle rows, caps, evidence
discipline and plan lifecycle. Use the workflow from P1.1; P2.1 establishes
and verifies the team's reproducible setup. The subject worker loads none of
that development scaffolding by default.

The initial row in each remedy phase opens one candidate's cycle. Add another
row per candidate after reading the preceding evidence; do not preselect a
stack. Screens explore; preregistered runs decide presets. A rejected candidate
closes with its evidence and no preset addition.

## Phase 1 — Repository and dependencies

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P1.1** | Infrastructure: `github.com/satyrn-ai/satyrn-pi` seeded from this tree, npm and Python package boundaries and dependency locks, default test commands, ignored runs, and a repository-weight check. Both package names are `satyrn-pi`. | Publishing empty packages; worker behaviour; eval execution; OpenCode. | proposed — first implementation cycle. |

## Phase 2 — SDD setup

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P2.1** | Infrastructure: a recorded Superpowers revision and contributor Pi skill setup; root rules index, verbatim source rules, glossary/pathology records, backlog and close checklist; re-earned cap/lifecycle/evidence checks, default-test tripwire and one-way import check. Demonstrate a new contributor's agent finding the rules and following a cycle. See [applicability](docs/rules-applicability.md). | Education material; transplanting source tests; loading contributor skills into the subject worker; runtime measurement claims. | proposed — after P1.1; use Superpowers/SDD from the first cycle, then prove this repeatable setup and its gates. |

## Phase 3 — Zensical documentation

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P3.1** | An installer/contributor documentation site over plain Markdown sources, with working navigation, glossary linking and a passing Zensical build. Ben owns navigation and onboarding review. | Learning centre, lessons, challenge and gamification; runtime setup claims. | proposed — after P2.1. |

## Phase 4 — Getting Started setup: llama.cpp

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P4.1** | Getting Started setup for the Q4_K_M subject on llama-server b12066 at `127.0.0.1:8001`; record the actual GGUF digest, platform artifact and serve flags, and demonstrate a response on the documented reference platform. See [rig](docs/superpowers/research/2026-11-16-reference-rig.md). | Eval-managed server lifecycle; pod provisioning; implying other hosts or historical runs used this exact build. | proposed — after P3.1; document other platforms as unverified until exercised. |

## Phase 5 — Eval CLI

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P5.1** | The Python CLI entry `uvx satyrn-pi eval --suite <name>`, worker resolution via explicit `--worker` else installed npm package, printed and recorded resolution, `--base-url`, and `runs/` output contract. Prove resolution and orchestration with fixtures; actual suites and model arms land next. | Server or pod provisioning; selecting arbitrary workers on ambiguity; a fake run reported as a model measurement. | proposed — after P4.1; document checkout invocation and package artifact verification. |

## Phase 6 — Suites

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P6.1** | Preserved Easy/Medium/Hard fixtures and expectations, rewritten grading, witness qualification, grade identity and score provenance. Easy's four-check inherited grade remains primary. Qualify expected/observed acceptance feedback and distinguish gate identity from oracle grade, using [Andre's supplement](docs/superpowers/research/2026-11-16-upstream-acceptance-feedback.md). See [grading](docs/superpowers/research/2026-11-16-grading-compatibility.md). | Silently correcting historical grades; merging gate-message versions; enabling a settle/redispatch remedy; Education challenge UI. | proposed — after P5.1; qualify verdicts and feedback before trusting a model score or later gate. |

## Phase 7 — Vanilla-Pi arm

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P7.1** | A real eval arm with only Vanilla Pi and the recorder, no worker or remedies; isolated settings, resolved model/host/grader provenance, and a recorded baseline. Fix the intended context-file policy and other run settings before deciding runs. | Preset promotion; a worker-loaded arm described as vanilla; inherited rates presented as new-stack measurements. | proposed — after P6.1; screens precede any preregistered comparison. |

## Phase 8 — Baseline worker

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P8.1** | The thin worker command and mode machinery: subject-model switch, pre-marker history integrity, span record and parent-model restoration, plus an eval arm and package-boundary verification. Here baseline means the thin worker alone. | The source `baseline-worker` remedy bundle; default prompt replacement, guards, facts, tool narrowing or delegation nudges. | proposed — after P7.1; measure the rewritten worker before crediting remedies. |

## Phase 9 — Finish Getting Started

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P9.1** | An installer walkthrough from the npm Pi package and running server to a completed worker task, plus a contributor walkthrough using uvx eval with the resolved worker printed in the record. Exercise the package artifacts, not just checkout-relative paths. | Requiring installers to clone; a course; claiming rates from onboarding smoke runs. | proposed — after P8.1; Ben owns onboarding acceptance. |

## Phase 10 — Easy remedies

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P10.1** | One agnostic remedy candidate addressing an observed Easy failure; its additive selection interface for live Pi and eval; screen evidence and a preregistered promotion decision if warranted. Follow [credit](docs/superpowers/research/2026-11-16-remedy-credit.md). | A prefilled Easy stack; multiple new remedies in one cycle; suite-specific answers. | proposed — after P9.1; add one row per further candidate, and close the phase with the measured preset or an explicit unmet tier. |

## Phase 11 — Medium remedies

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P11.1** | One agnostic remedy candidate for an observed Medium failure, measured against the declared baseline with grade and cost meanings fixed. Record previously earned units. If acceptance redispatch is chosen, use the qualified expected/observed feedback contract from [the upstream supplement](docs/superpowers/research/2026-11-16-upstream-acceptance-feedback.md), with its own gate identity and preregistered promotion rule. | Assuming Easy gains transfer; filling a preset by inheritance; multiple new remedies per cycle; promoting Andre's n=3 screen as a rate. | proposed — after phase 10 closes; further candidates each get a row and promotion decision. |

## Phase 12 — Hard remedies

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **P12.1** | One agnostic remedy candidate for an observed Hard failure, its evidence and promotion decision, then a tier verdict against the preregistered rule. A documented failure to reach the target is an admissible outcome. | Fine-tuning, DPO or SFT; a reserved model-training phase; retrospective changes to n or grading to obtain a pass. | proposed — after phase 11 closes; further candidates each get a row. |

## Closing and release

Each cycle uses the mapped source closing checklist. A phase closes when its
declared deliverable has a reviewed outcome, including negative findings;
closing does not itself publish either package or claim a pass rate. Define
both-package release checks in the relevant cycle before publishing.

## Ongoing development after the port

Keep the Superpowers/SDD cycle and repository extensions in operation after
phase 12. Add a cycle to the relevant phase, or a new phase for a new body of
work, before implementation; record its Ships/Excludes and link any existing
decision it would reopen. Close it with evidence, fresh verification, Nicola's
PR approval and the mapped closing checklist. Archive closed plans and retain
their roadmap rows; move deferred work to the backlog with reopen conditions.

Continue one remedy per feature cycle, screens before deciding runs, and
preregistered promotion rules. Revisit the contributor skill setup when its
tools change, using a bounded infrastructure cycle. The roadmap remains the
current work index, not an archived migration checklist.
