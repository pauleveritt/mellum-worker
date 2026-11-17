# Brief: Satyrn Pi

**Read this first.** Satyrn Pi makes a small local model a bounded coding worker
inside Pi, and publishes the evidence that says which of its parts earn their
place. This file carries the judgement behind that: what we are building, what
we refuse to build, the trap three prior attempts fell into, and what is already
decided. Open questions have linked research owners at the end; their notes
state which phase needs an answer and what evidence is still missing.

Evidence re-opens a decision. Measurements below link to their source record.
Record a dated correction when evidence invalidates a claim; preserve the
earlier reasoning alongside it.

## What we are building

One repository, two published artefacts, three audiences.

- Repository: `github.com/satyrn-ai/satyrn-pi`
- npm `satyrn-pi` — the Pi package. Install it and you have the worker.
- PyPI `satyrn-pi` — the measurement CLI, run as `uvx satyrn-pi eval`.

The repository already exists, public and MIT-licensed (`Copyright (c) 2026
Satyrn AI`), holding nothing but `LICENSE` and an `Initial commit` from
2026-11-11; phase 1 populates it rather than creating it. Both package names are
unclaimed on their registries. Both are published from CI using trusted
publishing, so no person holds a release token and a release is not a task that
waits on one person's hours.

The product starts with **Vanilla Pi plus explicit remedies**. Vanilla Pi
loads no worker at all. On top of it sits a thin worker whose only job is to
switch the session to the subject model and record the run. Everything else is
an explicit, inspectable remedy under `remedies/<kind>/` that a user or a preset
switches on. Nothing is bundled, so nothing has to be credited on faith.

The public progression is **Vanilla → Base → Easy → Medium → Hard**.
Vanilla is Pi plus a trace recorder. Base adds the thin worker and an explicit
common remedy preset, initially empty. Easy adds its earned remedies to Base;
Medium adds to Easy; Hard adds to Medium. The worker itself stays thin.
These names say what is enabled; they do not claim a suite already passes.
A suite names the tasks being graded: Vanilla and Base can both run the Easy
suite. A preset stores the remedy list; Vanilla loads none. Use these direct
names without an extra glossary concept called Stage. The
[glossary](docs/glossary.md) defines the product terms; the
[vocabulary review](docs/superpowers/research/2026-11-16-vocabulary-review.md)
maps historical names. Baseline Worker is retired as a product label.

It owns: the worker extension and its mode machinery; the remedies and the
prompt fragments; the presets; the eval CLI, the suites, and the run records;
the documentation that serves both an installer and a contributor.

It does **not** own: the learning centre, lessons, the challenge, or
gamification — those belong to Satyrn Education. It does not own the model or
its weights, including any fine-tuning, DPO or SFT pipeline; that work is
deferred with no design in this cycle and no phase reserved for it. It does not
support a harness other than Pi: OpenCode support is removed completely, which
also removes the install-path constraint that shaped the source repository.

## Who it serves

- **The installer.** Finds `satyrn-pi` on npm, runs one install line, and gets a
  worker they can talk to. They will never clone the repository.
- **The contributor.** Clones, runs `uvx satyrn-pi eval`, and can reproduce or
  dispute any published number. Andre and Paul are the implementers, at roughly
  20 and 10 hours a week, working with agents rather than by hand.
- **The team lead.** Nicola approves pull requests and owns the decisions, at
  6–8 hours a week. Ben owns documentation and onboarding, at roughly 10.

Two consequences follow, and both are constraints on the roadmap. Nicola's hours
are the bottleneck, so a phase must land as a small, reviewable merge rather
than a branch that arrives whole. Ben's hours are real capacity, so documentation
is a lane with its own cycles, not a phase squeezed in at the end.

## Provenance

Seeded from `mellum-worker` at commit `0e4a9b68` (2026-11-13). That repository is
evidence, not source.

**Supplemental source review, 2026-11-16:** after fetching `origin/main`,
Andre's `3e20e161` and `41fa54d0` (2026-11-15) add clearer Medium acceptance
feedback and its n=3 screen. The [upstream review](docs/superpowers/research/2026-11-16-upstream-acceptance-feedback.md)
records their exact scope, phase-6 qualification work and later remedy-cycle
implications. The original source pin, preserved rules and historical grades
remain attached to their original revision; the supplement does not rebase them.

**Provenance drift, 2026-11-16:** `origin/main` is exactly two commits past the
pin — `3e20e161` and `41fa54d0` — and they are the two the supplement above
reviews; nothing further has landed. The pin stays `0e4a9b68` rather than
following the branch, because moving it would reopen the grades, fixtures and
screens already reviewed at that revision, and the supplement already carries
what those two commits change (`ladder/fixtures/acceptance/test_medium.py` and
its new message tests). Reopens when a phase needs a commit past those two, and
then as one named adoption with its own review, not as a background refresh.

**What crosses verbatim:** the prompt source, the suite fixtures and the
graders' expectations, the measured run records, the guards' policy and their
thresholds, and `docs/sdd.md` together with the project rules. The two rule
documents are staged byte-for-byte as [docs/sdd.md](docs/sdd.md) and
[source AGENTS.md](docs/provenance/mellum-worker-AGENTS.md). Phase 2 installs
their effective rules and re-earns their gates. The separate
[applicability document](docs/rules-applicability.md) states precedence, path
mappings and exclusions; it does not edit the preserved originals.

**What is re-earned:** every implementation file, and the tests that prove it,
through the Superpowers and SDD workflow below. Reading
the old code while writing the new one is expected. Transplanting it without a
recorded decision is not, because the point of the rewrite is that a lead who
re-derived a behaviour can change it, and a lead who inherited one cannot.

A phase that finds it needs to know something the old tree never wrote down may
send one bounded question back to that repository. That is a legitimate errand,
not a failure of this brief.

## How we develop: Superpowers, SDD and the roadmap

**Superpowers is the contributor development workflow for the port and for
ongoing development.** It supplies the skills for brainstorming, writing specs
and plans, executing an approved plan, test-first development, systematic
debugging, review and verification before completion. Contributors and their
agents use those skills; the subject Mellum worker does not acquire them by
default. The contributors' model rig remains separate from the measured subject.

The [SDD process](docs/sdd.md) records how this repository applies that workflow,
under the [applicability rules](docs/rules-applicability.md). P1.2 first records
the worker/eval responsibilities, shared run contract and small vocabulary in
`docs/domain.md` and `docs/glossary.md`, including the numeric jargon budget and
checker scope. This is a bounded documentation cycle after repository setup;
later feature cycles may refine it with a recorded reason. Phase 2 establishes
the contributor setup: select and record a Superpowers revision, make its skills
available in the contributors' Pi rig, and prove a new contributor's agent can
find the governing rules and follow a cycle. Copying process prose alone does
not complete that phase. No new development framework is needed.

The loop is **brainstorm → spec → plan → execute → review/close**, sized to
the change. Brainstorming retrieves existing decisions and evidence first and
ends with the human partner's approval before implementation. Product behaviour
changes get a spec; work large enough to need a plan gets one. Execution follows
that approved scope, with new tests shown to fail before the code that passes
them. Bugs use systematic diagnosis; completion claims need fresh verification.
Review checks both the agreed behaviour and implementation quality; Nicola
approves PRs. Screens (a few exploratory runs) retain the SDD exception: no
preregistration, spec or plan is needed just to explore, but a deciding run is
preregistered.

**The roadmap conventions are repository extensions to that workflow.** A
phase contains feature cycles. Each cycle has an ID and a `Ships`, `Excludes`
and `Status` row, linked to its spec, any plan and its evidence. `## Now` is a
pointer; deferred work lives in a backlog entry with a reopen condition. Caps,
plan front matter (`phase`, `feature_cycle`, `cycle`, `lifecycle`), a closing
`## Result` and immutable archived plans keep intent, evidence and current
state distinct. Phase 2 re-earns their executable checks; they are development
rules, separate from Pi runtime extensions and remedies.

At cycle close, update the row and `## Now`, remove resolved backlog entries,
update glossary and observed pathologies when warranted, reconcile the
changelog, verify linked claims, run the required checks and archive the closed
plan. The [source closing checklist](docs/sdd.md#closing-a-feature-cycle) and
its mapped destinations govern the details. A negative finding can close a
cycle without shipping a remedy or claiming a win.

The twelve phases organise this port; they do not end SDD. Subsequent features,
maintenance, bugs and new remedy candidates use the same skills and records.
Add cycles to the relevant phase, or a new phase for a new body of work; keep
closed decisions and evidence retrievable. Reopening a measured setting still
needs applicable eval evidence, and promoting a default still needs the
preregistered decision rule. Finishing the port is not a switch to an informal
backlog or a licence to prefill the next preset.

## The trap we are avoiding

The [satyrn-engine brief](https://github.com/pauleveritt/satyrn-engine/blob/9aecfb513be3211d5f5753bf778807ccecfd76ca/BRIEF.md#L71)
describes prior attempts becoming engineering efforts about orchestration —
hangs, timeouts, gating, graders. That is inherited judgement, not a new
measurement of those attempts. Our source-tree inspection found 32 top-level
TypeScript files in `extensions/` and 2,245 tracked files under `runs/`, of
which 2,226 were inside a run workspace's `.venv`. File count does not establish
which extensions are unused. The [inspection record](docs/superpowers/research/2026-11-16-source-inspection.md)
carries the commands and distinguishes checkout-local Git size from revision
contents.

- **One phase at a time.** A tangent goes to the backlog, never into the current
  cycle.
- **No machinery ahead of the contract it serves.** A framework arrives when
  three concrete cases need the same shape, not before.
- **Concept budget.** The people who build this work 6–20 hours a week. If a
  document needs a term they cannot absorb, the term goes, not the contributor.
- **Repository-weight budget.** A run record is `run.json` and its score. Raw
  traces, stdout and workspaces are release assets, never commits. Check weight
  from phase one.

## Binding rules

1. **Verify, don't assert.** Claims cite `file:line` or a record; a number
   carries the command that recomputes it.
2. **Each feature cycle ships one user-visible behaviour** and names what it
   excludes. A phase contains cycles; an infrastructure cycle says so in its row.
3. **Default tests use no model, no network, no subprocess.** Process behaviour
   lives in marked integration tests that CI does not run. A planted
   process-spawning test must fail the build, and that tripwire is proven once.
4. **A refusal test has a sibling success test.** Demonstrate both the permitted
   and refused behaviour, so an unrelated failure cannot satisfy a refusal test.
5. **Imports run one way.** The worker package never imports the eval package;
   the check is mechanical. Evidence may flow into a run record; lab code may
   not flow into the shipped path.
6. **A test seam is the extension seam.** If it is injected to test it, it is the
   extension point. There is no second plugin system.
7. **Data over code.** A remedy is a file. A preset is JSON. Extending means
   adding a file, not subclassing a framework.
8. **Docs land with the cycle**, in the same pull request: the roadmap row's
   status, a glossary entry for any concept the cycle introduced, and a
   changelog line under `[Unreleased]` for user-facing changes. Internal SDD
   records retain the source rule's exemption.
9. **The copied gates stay green.** The caps in `docs/sdd.md`, the feature-cycle
   lifecycle and the closing checklist arrive with working tests.
10. **Prefer familiar, accurate vocabulary.** Use established terms where they
    describe the same thing: suites, tasks, runs and presets. Use Vanilla → Base
    → Easy → Medium → Hard directly, without teaching another label for the
    progression. A preset names a remedy list; a complete experimental arm also
    includes the worker state and run settings. Explain research terms where
    needed and preserve their meaning. Apply this rule throughout porting and
    ongoing work, with P1.2's jargon budget enforced in phase 2; keep historical
    records and copied rules intact, with dated mappings for changed names. The
    [vocabulary review](docs/superpowers/research/2026-11-16-vocabulary-review.md)
    records the rationale and avoids claiming one universal industry dictionary.

## Architecture, already decided

- **Pi only.** No second harness, and no install path that exists to please one.
- **Vanilla Pi plus the trace recorder is the baseline.** Nothing else loads.
- **The worker bundles nothing** — the command tool and the mode machinery.
  It does not swap the system prompt, narrow the tools, add project facts, or
  install a guard.
- **Everything else is a remedy** under `remedies/<kind>/`: `guard`,
  `nudge`, `context`, `prompt`, `tool`, `check`, `workflow`. The prompt is a kind
  of its own: small fragments, added one at a time. A remedy encodes no
  suite-specific answer.
- **Presets are results.** Base, Easy, Medium and Hard start with empty remedy
  lists and are filled only by runs on this repository's own stack. This
  deliberately differs from retaining the
  source presets. Its Easy ladder records incremental prompt and guard screens,
  including n=6 results; those are leads, not settled rates. Andre explicitly
  refused emptying the source presets. We preserve that evidence and disagreement
  in the [credit policy](docs/superpowers/research/2026-11-16-remedy-credit.md).
- **Presets are flat, self-contained JSON lists.** `base.json`, `easy.json`,
  `medium.json` and `hard.json` each list all remedies for that name, in load order.
  No includes and no nesting machinery. A test checks that each successive
  preset retains every remedy of its predecessor; adjacent lists may be equal.
  Record the complete resolved list and order for each run. Cumulative lists
  do not establish that gains transfer: measure each preset on its target suite.
  A shared remedy earns a Base addition through its own cycle and promotion
  decision, with affected later presets requalified before any new claim.
- **A remedy is a TypeScript module** exporting `meta` and its hook, one
  file per remedy under `remedies/<kind>/<name>.ts`. The loader that resolves a
  remedy name to a file, and the switch that turns one on in a live session, land
  in the same cycle as the first real remedy: the contract earns its shape from
  a concrete remedy rather than from a framework built ahead of it.
- **The graders ship inside the Python package**, because `uvx` cannot grade
  from a checkout it does not have, and they run from a copy outside the run's
  workspace, so the worker can neither read nor edit what grades it.
- **Subject model:** Mellum 2.1 12B-A2.5B Thinking,
  `JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M`, served by
  `llama-server` on `127.0.0.1:8001` (API base URL
  `http://127.0.0.1:8001/v1`). The reference server is **b12066**, the source
  installer's default. This is an explicit choice among the source's differing
  configurations, not a claim that every historical run used it. The
  [reference-rig record](docs/superpowers/research/2026-11-16-reference-rig.md)
  names the sources and phase-4 verification requirements.
- **Hosts:** local `llama-server` for screens; a rented pod (RunPod or Vast) for
  batches. Rented batches are a separate policy departure: Andre refused them
  for the source repository. Use the same model quant and server version;
  record platform-specific binaries or image digests, flags and hardware in
  each host card. Matching those inputs does not establish host equivalence.
  [Batch research](docs/superpowers/research/2026-11-16-batch-hosts.md) owns
  cost and comparability; no rented configuration is qualified here yet.
- **Measurement:** `uvx satyrn-pi eval --suite <name>`. It resolves the worker —
  an explicit `--worker` path, or else the installed npm package — prints and
  records that resolution, assumes a server at `--base-url`, and writes
  `run.json` under `runs/`. An ambiguous resolution fails loudly instead of
  choosing. Server installation, startup, shutdown and pod provisioning are
  external to `eval` throughout these twelve phases.
- **Grading compatibility:** copy the suites and grader expectations unchanged.
  The inherited grade remains the primary reported number: Easy has four
  expected checks. A stricter or corrected grade is separately named and
  versioned, reported beside it. Preserve old records verbatim with their
  original grade and metric meanings. The
  [grading record](docs/superpowers/research/2026-11-16-grading-compatibility.md)
  owns qualification and version mapping; new grades do not rewrite old scores.
- **The contributors' rig is not the subject.** The implementers run Pi with
  DeepSeek 4.1 Flash as the primary model and Kimi K3 for re-planning. That is
  how the work gets done; it says nothing about what Satyrn Pi is for, and the
  brief keeps the two apart on purpose.

## Where to start

[ROADMAP.md](ROADMAP.md) carries twelve phases, in this order: repository setup,
including P1.2's domain and vocabulary agreement; spec-driven development setup
that installs the preserved process and rules; the Zensical documentation site;
Getting Started's setup section for `llama.cpp`; the eval CLI; the eval suites;
Vanilla; Base; the rest of Getting Started; then remedies as three phases —
Easy, Medium, Hard — one remedy per feature cycle.

Read [the applicability rules](docs/rules-applicability.md) and
[`docs/sdd.md`](docs/sdd.md) before writing a spec, a plan or a roadmap row.
Read `ROADMAP.md`'s `## Now` before starting work. The roadmap is planning
input; each cycle still earns its spec, any needed plan, implementation and
review. Nothing in this staging tree claims a product phase has shipped.
Use the [development workflow](#how-we-develop-superpowers-sdd-and-the-roadmap)
for the first porting cycle as well as work after phase 12; phase 2 makes it
reproducible for the full team rather than postponing its use until then.

## Decisions the research documents own

- [Reference rig](docs/superpowers/research/2026-11-16-reference-rig.md): resolve
  and record the actual GGUF digest and platform artifacts before phase 4 closes.
- [Grading compatibility](docs/superpowers/research/2026-11-16-grading-compatibility.md):
  qualify the rewritten graders against preserved expectations and version any
  additional grade before phase 6 closes.
- [Remedy credit](docs/superpowers/research/2026-11-16-remedy-credit.md): decide
  which remedies earn each preset through preregistered runs in phases 10–12.
- [Batch hosts](docs/superpowers/research/2026-11-16-batch-hosts.md): establish
  cost and any claimed comparability before the batch they govern; fix n and
  the decision rule before a deciding run.
