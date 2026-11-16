# Learner glossary audit

## What is measured / what is conjecture

**Date:** 2026-11-16. **Scope:** glossary definitions, learner pages and relevant
code/tests, inspected at `3989be7371e73f5cbc1710ead13c8063d8e792d7`.
This collects porting proposals; it changes no source-product behaviour.

**What is measured:** the glossary contains 92 entries, including 31 AI terms.
The installed parser maps Easy/Medium/Hard to Challenge and bare Pi to Vanilla
Pi. **What is conjecture:** that the proposed cuts help learners; no learner
study or model run was performed.

Sources: the repository team's [glossary](../../../learn/glossary.md),
[Getting Started](../../../learn/getting-started/index.md),
[evidence policy](../../../learn/about/evidence.md),
[introduction](../../../learn/introduction/index.md),
[harness](../../../learn/code/harness.py) and
[tests](../../../tests/learn-site.test.mjs), accessed 2026-11-16.
Citations below refer to that revision; proposal numbers match
[the detailed proposals](2026-11-16-proposals-for-andre.md#proposals-for-andre).

## Findings

### 2–6: progression and conflicting names

Baseline Worker means the thin worker in `learn/glossary.md:99`, but the shipped
bundle in `learn/getting-started/working-with-pi.md:179`. The scoreboard even
says “Baseline Worker, vanilla arm” (`learn/scoreboard.md:29`). Preserve each
record's revision and explicit settings; a global rename would equate different
runs.

The harness distinguishes Vanilla, inactive-extension `bare` and active worker
(`learn/code/harness.py:133`). Its loader reads exactly the named preset's list
(`:499`); `baseline-worker` contains five remedies, Easy a different four.
Cumulative presets are a port decision, not existing implicit inheritance.

“Base Pi” already means Pi without the worker
(`learn/getting-started/base-pi-on-llamacpp.md:10`). Rename that setup Vanilla
in the port to avoid collision with the proposed Base.

### 7–8: navigation and contributor vocabulary

Learning Center, Track, Lesson and Before and after define ordinary page
structure (`learn/glossary.md:11`, `:154`). Remove those prerequisites.
Six-step template, Interpretation, Phase and Feature cycle belong in authoring
guidance (`:24`, `:29`, `:42`, `:49`).

Explain Hook, Event and Callback together in the extension example
(`learn/getting-started/extensions.md:44`). Retain Project trust where users
choose what to load, including its limit: it does not confine tool access
(`learn/glossary.md:342`).

### 9–11: remedies, nudges and failures

Remedy and Remedy unit describe the same change at different detail levels
(`learn/glossary.md:133`); merge them. Keep Tool and Guard as useful behavioural
distinctions.

Nudge and Empty-final nudge both describe the empty-turn remedy
(`learn/glossary.md:173`), yet `remedies/nudge/redirect-followed.ts:1` reacts to
command output. Define the general corrective message once, with triggers and
limits beside each remedy (`remedies/nudge/empty-turn.ts:12`).

Prefer plain failure descriptions to Pathology (`learn/glossary.md:84`). The
catalog correctly includes harness and test defects (`learn/pathologies.md:17`);
those should not sound like model defects.

### 12–14: roles, programs and attempts

Parent model explicitly aliases Main agent (`learn/glossary.md:369`). Use one
main-model explanation and call its Handoff block the worker's report (`:374`);
that does not make the optional report-collapse remedy a default.

Agent is a system using a model in the glossary (`:383`), but “a specific tool”
in the introduction (`learn/introduction/index.md:50`). Pi and the evaluation
program are both called a harness (`learn/glossary.md:331`, `:427`;
`learn/getting-started/base-pi-on-llamacpp.md:11`). Explain each program's job
before architecture terminology. Keep the mini-harness exercise and historical
ladder distinctions where needed.

Session means a suite attempt in `learn/glossary.md:276` and a resumable
conversation in `learn/getting-started/working-with-pi.md:84`. Use run for the
attempt; retain Pi session for the conversation and preserve historical fields.

### 15–16: metrics and scoring

Requests and turns receive the same `provider_request` count
(`learn/code/harness.py:996`). Label it Model requests and replace Wall with
Elapsed seconds. Dividing time by prompt count (`learn/glossary.md:320`) does
not control for different work or accumulated context.

Put Expected IDs, Failed checks and Checks did not run beside the score
(`learn/glossary.md:285`, `:305`, `:312`). Preserve their distinctions: the
harness records both missing passes and whether grading ran
(`learn/code/harness.py:1060`). Put Qualification with grader validation.

Canary detection scans traces for a marker or suite path
(`learn/code/harness.py:798`); it does not prove confinement. Keep hidden grading
distinct from worker-facing feedback: a corrective gate can pass a wrong build
(`learn/lessons/hard/the-gate-is-a-proxy.md:39`).

### 17: evidence labels

Cited means oMLX/mlx-lm evidence ranked above Screen in the glossary
(`learn/glossary.md:69`), but uses a pre-2026-10-25 cutoff on the evidence page
(`learn/about/evidence.md:12`). That page also extends Reference-run to a
lesson's own challenge (`:16`), a scope missing from the glossary.

Consolidate the explanation while preserving exploratory versus preregistered
runs, sample size, fixed scoring/decision rules and linked records. Backend,
citation age and experimental strength are different questions.

### 18–19: techniques and AI background

Strip thinking removes earlier reasoning; Reduced thinking requests shorter
new reasoning (`learn/glossary.md:195`, `:211`). Keep the behaviours distinct,
but explain them with their experiments, alongside sampling, spec-layout,
loop-prevention and acceptance-gate techniques.

Working memory generalises a causal explanation (`learn/glossary.md:447`) from
A12's particular ablation (`evals/ablation-summary.md:23`). Say previous
reasoning operationally and retain the result's host/model/settings.

Keep practical AI basics; defer embeddings, vectors, multimodality, RAG and
training concepts until relevant material needs them. Explain token IDs and
tokenizers alongside tokens when needed. The port has no training phase.

### 20–22: links, tests and stale facts

Easy/Medium/Hard alias Challenge; bare Pi aliases Vanilla despite the distinct
`bare` option (`learn/glossary.md:36`, `:110`). The installed parser confirms
these mappings. Review aliases for meaning, not merely valid links.

Tests require Baseline Worker, Strip thinking and both nudge headings
(`tests/learn-site.test.mjs:52`). Replace obsolete heading requirements in the
port with budget/link checks, allowing historical citations and ordinary words.

The mini harness is step 3 in the glossary (`:254`) but step 4 in Getting
Started (`learn/getting-started/index.md:13`). The Challenge table adds an eighth
phase (`learn/challenge/index.md:51`); Hard's fixture has seven phases plus four
migration requests (`learn/code/suites/hard/base/specs/roadmap.md:3`, `:65`).
Correct port explanations; preserve fixtures and old grades. Keep changing
counts, settings and results in their owning references.

## Disposition of all 92 entries

These are proposed documentation changes, not feature removals.

| Group | Current headings | Recommended treatment |
| --- | --- | --- |
| Navigation | Learning Center; Track; Lesson; Before and after; Challenge | Drop ordinary labels; keep Challenge in Education. |
| Contributor process | Six-step template; Interpretation; Phase; Feature cycle; Lesson check; Qualification | Move to authoring, workflow or grader-validation guidance. |
| History/comparison | Baseline lesson; Baseline Worker; Arm; Floor; Ladder; Rung | Preserve records; explain historical mappings outside onboarding. |
| User choices | Vanilla Pi; Remedy; Remedy unit; Preset | Keep Vanilla/Remedy; merge Remedy unit; explain preset files where selected. |
| Remedy mechanisms | Guard; Nudge; Empty-final nudge | Keep distinct behaviours; merge duplicate nudge definitions. |
| Failure catalog | Pathology | Describe failures plainly, retaining evidence. |
| Particular techniques | Ablation; Loop breaker; Strip thinking; Live-server spiral; Reduced thinking; Exit-gate; Architect split; Spec variant; Greedy; Sampled; Working memory | Explain with experiments/remedies; bound interpretations by evidence. |
| Programs and attempts | Mini harness; Eval suite; Session; Pi; Harness; Eval | Name Pi/eval first; distinguish suite, run and Pi session. |
| Scores and metrics | Grader; Expected IDs; Canary; Turns; Failed checks; Checks did not run; Wall; Output tokens | One scoring reference; preserve distinct failure states. |
| Extension authoring | Pi extension; Project trust; Hook; Event; Callback | Explain loading/trust at use; introduce event-handler vocabulary together. |
| Delegation | Main agent; Parent model; Handoff block | One main model and the worker's report. |
| Practical basics | Tool; Agent; Agent loop; API; Context; Context window; LLM; Prompt; System instructions; Token; Tool calling | Combine related explanations; introduce when needed. |
| Explain in place | Completion; Inference; Latency; Weights; Temperature; Token ID; Tokenizer | Explain at use rather than as prerequisites. |
| Optional background | Embedding; Fine-tuning; Grounding; Hallucination; Agent memory; Multimodal; N-gram; Pretraining; RAG; Training; Vector | Defer to relevant optional material. |
| Evidence labels | Badge; Screen; Cited; Reference-run; Conjecture | Consolidate explanation; separate experimental status from provenance. |

**Port follow-up, 2026-11-16:** the initial staging glossary had 14 entries,
including historical names. The [vocabulary review](../../../satyrn-pi/docs/superpowers/research/2026-11-16-vocabulary-review.md)
reduces its core to five definitions and retains source mappings separately.

## Verification and limits

Count entries with `rg -c '^### ' learn/glossary.md`; the AI section contributes
31. Every heading appears once in the table's Current headings cells.

Aliases were checked using `uv run --no-sync python` and the installed
`zensical_glossary.extension.GlossaryStore`, loading heading level 3.
Literal text searches were discovery aids: absent matches do not establish
that a concept is unused.

P1.2 in the port roadmap specifies the domain description, vocabulary and
numeric budget; phase 2 implements the check. Removing headings also requires
reviewing links, navigation, tests and anchors. Education may retain background
that Satyrn Pi onboarding does not need.

## Recommendation

Keep the concrete duplicate and definition findings; treat curriculum cuts as
proposals. Review one learner path—install, run a suite, read results, try a
remedy—and retain only the vocabulary that path needs.

## What would falsify this

A learner task requiring a proposed-to-cut term separately would falsify that
cut. Record dated corrections when source changes supersede findings.

## Risks

Word removal can hide worker-state, feedback/grading and failed/not-run
distinctions. Preserve those meanings; inspect page prose as well as glossary
size so jargon is not merely relocated.
