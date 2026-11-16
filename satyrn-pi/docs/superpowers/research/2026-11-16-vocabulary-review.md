# Port vocabulary review

## What is measured / what is conjecture

**Date:** 2026-11-16. **Scope:** evaluation vocabulary, proposed Harbor naming
and terminology acceptance for the port. Changes here apply to the porting
plan and proposals for Andre, not the source product.

**What is measured:** the source uses numbered tasks under `ladder/`, explicit
remedy lists and distinct worker states. The primary documentation below shows
overlapping evaluation vocabulary, not one universal dictionary.
**What is conjecture:** which wording learners will find easiest. Naming
recommendations are not measured learning outcomes.

## Proposed Harbor naming

Use Harbor as the reference for evaluation concepts, with Hamel Husain and
Shreya Shankar's guidance informing the evidence-driven improvement process.
These are proposed naming changes for P1.2 to confirm, not a decision to adopt
the Harbor implementation.

| Current wording | Proposed wording | Boundary |
| --- | --- | --- |
| Ladder / eval suite | Dataset | A collection of tasks. |
| Rung / coding task | Task | Instructions, starting environment and verification. |
| Run / repetition for one task attempt | Trial | One agent's attempt at one task. |
| Run for the whole evaluation | Job | A collection of trials. |
| Grader | Verifier | Evaluates the work; feedback and hidden scoring remain distinct contracts. |
| Trace for conversation/actions | Trajectory | Conversation and action history; other telemetry keeps its own meaning. |
| Agent conflated with model | Agent | The task-completing program; Pi plus selected extensions, separate from its model. |

The staged glossary and implementation rows still use suite/run/grader/trace.
P1.2 confirms this proposal and reconciles those active definitions before
implementation. Preserve the already-agreed `eval --suite` and `run.json`
interfaces unless separately changed; keep historical records and source paths
intact. Vanilla → Base → Easy → Medium → Hard and preset retain their meanings.
Where ambiguous, qualify Easy as a dataset or preset.

## Meanings to preserve

1. **Source tasks have different shapes.** `ladder/ladder/rungs.py:261`
   registers standalone tasks and, at `:281`, AgentClinic steps. Map each source
   ID to the port's task boundary rather than assuming every rung is an entire
   application or dataset.
2. **Frameworks use different boundaries.** Harbor defines tasks, datasets,
   trials and jobs; EleutherAI uses tasks and groups; Inspect tasks combine
   datasets, solvers and scorers. These are reference models, not a universal
   dictionary. Each adopted term needs its local meaning explained once.
3. **Preset is narrower than a complete run.** It stores remedies, not the
   worker state, model, host or suite. Vanilla loads no remedy preset. Use
   Vanilla → Base → Easy → Medium → Hard directly rather than replacing every
   occurrence of Stage with Preset.
4. **Preserve experimental meaning.** Screen is the copied SDD term for
   exploratory runs. Explain it in plain language; replacing it everywhere with
   Pilot run would not remove a concept. Keep preregistration requirements.
5. **Corrective feedback is not a request retry.** Acceptance redispatch sends
   failures back for further work. A retry can instead repeat a failed request.
   Explain the behaviour rather than treating the two as synonyms.
6. **Repetitions are not seeds.** A seed is a run setting. Report its value if
   controlled; n repeated attempts does not establish n different seeds.
7. **A blanket word ban is not a jargon budget.** Ordinary uses of stage or
   screen and historical citations need no new concept. Inventory the vocabulary
   taught in a declared scope; review semantics as well as counting terms.

## Port inventory

This inventory records semantic changes; Harbor renames above remain proposed.

| Wording | Port action |
| --- | --- |
| Stage as a defined product concept | Removed from the core glossary; use the five names directly. |
| Preset | Retain for the ordered remedy list; distinguish it from the task collection, proposed as dataset. |
| Floor | Use Vanilla or baseline in active product explanations; preserve source quotations. |
| Remedy unit | Use remedy in product explanations; file paths and historical wording retain their identities. |
| Tier | Say preset, task collection or integration tests according to meaning; avoid global replacement. |
| Recorder | Retain the component; distinguish conversation/action history from other telemetry. |
| Screen, arm, redispatch | Retain where research precision matters, with a plain explanation at first use. |
| Bare, Rung, Baseline Worker | Move out of the core glossary into the source mapping below. |

The core port glossary now defines Vanilla, Base, Remedy, Preset and Eval suite.
This is an inventory, not the numerical budget: P1.2 agrees the budget and its
scope; phase 2 implements its check. P1.2 also records worker/eval responsibilities
and the shared run contract in `docs/domain.md`. Detailed schema/CLI choices
still belong to their implementation cycles. Twelve phases remain.

## Port acceptance

The roadmap assigns these decisions to deliverables, rather than relying on
the source glossary or importing Education's vocabulary:

| Owner | Acceptance |
| --- | --- |
| P1.2 domain and glossary | Confirm the proposed Harbor names and update staged definitions and implementation rows consistently. Distinguish dataset/task from remedies and trial from job. Retain the agreed CLI/file interfaces unless separately changed. Use the five product names directly; reserve Base for the active worker plus its explicit preset. Merge Remedy/Remedy unit and Main agent/Parent model; call the handoff the worker's report. Set the jargon budget and scope. |
| P2.1 rules and checks | Enforce the budget and alias contract, not obsolete heading names or a blanket word ban. Allow ordinary words and historical citations. Keep observed model failures distinct from harness/test defects; label them plainly even where the preserved path says `pathologies.md`. |
| P3.1 site | Link canonical terms automatically; remove misleading Easy/Medium/Hard → Challenge and bare Pi → Vanilla aliases. Define a nudge once; put each remedy's trigger and limits beside its use, and extension hooks beside contributor examples. Ordinary words need no glossary entry. |
| P5.1 CLI and records | Following P1.2's naming decision, distinguish one task attempt from the job collecting trials and the saved Pi session. Use Model requests and Elapsed seconds, document counting/aggregation, and keep repetitions distinct from seeds. Aggregation does not make different datasets comparable. |
| P6.1 scoring | Explain scores together while distinguishing failures, tests that never ran, grader access and corrective feedback. Distinguish evidence strength from backend, citation age and provenance; corrective work after feedback is not a request retry. |
| P4.1 setup and P9.1 onboarding | Rename worker-free Base Pi setup to Vanilla Pi; omit historical product labels from the new user path. Keep workflow vocabulary in contributor guidance and counts/settings/results in their owning references. Show independent suite and remedy choices. |
| Education boundary | Lessons own specialised experiments and AI background when needed. The port does not copy that glossary or invent learner terms for Learning Center, Track, Lesson or Before and after. Preserve experimental distinctions in cited evidence, including removing old reasoning versus requesting shorter new reasoning. |

New remedy cycles apply the same rules to their own docs. Historical source
paths, IDs, records and copied rules remain intact. Later cycles may refine the
domain or vocabulary with a recorded reason and the corresponding budget and
link checks.

## Source mapping

| Source term | Meaning to retain when reading evidence |
| --- | --- |
| `--arm vanilla` | No worker extension. Source harness options and selected remedies must both be recorded. |
| `--arm bare` | Worker extension loaded, mode off; distinct from Vanilla and new Base. |
| `--arm worker` | Worker mode on; selected remedies still need their complete list. |
| `baseline-worker` | Explicit five-remedy reconstruction of the old bundle, not new Base. The prose label changed meaning across revisions. |
| `ladder/`, rung IDs | Historical runner and numbered tasks; preserve cited paths, IDs and records. |

These mappings come from `learn/code/harness.py:133`, `:499`,
`remedies/presets/baseline-worker.json` and `learn/glossary.md:99` at the
preserved source revision `0e4a9b6859cbe447adbca537c5738f24a862d214`.
Copied `docs/sdd.md` and source rules remain byte-for-byte unchanged.

## External evidence

Primary documentation, accessed 2026-11-16:

- EleutherAI, [Groups & Benchmarks](https://lm-evaluation-harness.readthedocs.io/writing_tasks/groups_and_benchmarks/),
  opening definition: named groups collect tasks and aggregate their metrics.
- UK AI Security Institute, [Inspect Tasks](https://inspect.aisi.org.uk/tasks.html#task-basics),
  Task Basics: dataset, solver and scorer form a task.
- Optuna contributors, [SuccessiveHalvingPruner 4.9](https://optuna.readthedocs.io/en/v4.9.0/reference/generated/optuna.pruners.SuccessiveHalvingPruner.html),
  `min_resource`: rungs are resource checkpoints in successive halving.
- Harbor, [Core concepts](https://docs.harborframework.com/core-concepts/index),
  Task through Trajectory: task instructions/environment/verifier, dataset task
  collection, agent program, trial attempt, job collection and trajectory history.
- Hamel Husain and Shreya Shankar,
  [What's a minimum viable evaluation setup?](https://hamel.dev/blog/posts/evals-faq/whats-a-minimum-viable-evaluation-setup.html),
  opening guidance: begin with domain-expert review and error analysis of outputs.

These support familiar task terminology and context-dependent meanings. They
do not prove that ladder/rung are never used for evaluations elsewhere.

## What would falsify this

A proposed rename that obscures a real worker state, grading distinction or
experimental setting should be rejected. A documented reader task requiring
another core term would justify revising the vocabulary and budget explicitly.

## Risks

Mechanical replacement can change meaning while reducing word counts. A
glossary-only budget can also push jargon into prose; review the learner path
and keep historical evidence readable through mappings.
