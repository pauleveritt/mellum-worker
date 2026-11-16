---
phase: P1
feature_cycle: P1.2
cycle: 1
lifecycle: active
---

# Plan: vocabulary agreement and its check

The plan for P1.2, the cycle that agrees the port's vocabulary budget, and for
the check phase 2 installs. The [vocabulary review](../research/2026-11-16-vocabulary-review.md)
carries the rationale and the proposed Harbor mapping; this plan carries the
work, including the gate, so neither is re-derived later.

## What is decided here

| Term | Decision | Why |
| --- | --- | --- |
| `Stage` | Not a product concept. Use Vanilla → Base → Easy → Medium → Hard directly | An umbrella label every reader must learn, for a list they can just name |
| `floor` | Vanilla or baseline, in product prose | Vanilla is both the minimum configuration and the comparison arm |
| `remedy unit` | remedy, in prose | One concept, one word; the path keeps `remedies/` |
| `tier` | preset, task collection or integration tests, by meaning | One word was carrying two axes |
| `screen`, `arm`, `redispatch` | Retained; plain explanation at first use | They carry distinctions the standard words lose |
| `ladder`, `rung` | Source-mapping only; never taught as product choices | Names an axis the source does not have: the model is fixed, the task varies |
| `recorder` | Retained; conversation/action history is the trajectory | The component has no standard name; the data it writes does |
| Dataset, task, trial, job, verifier, agent | Proposed for P1.2, per Harbor | Industry vocabulary already in use for this exact domain |

Ladder and rung are not standard evaluation vocabulary. In ML a *scaling ladder*
means a series of model sizes, and on a leaderboard it means a ranking; here the
model is fixed and the task composes — the opposite axis. `rung` also carries
two meanings in the source: a stage and a single task (`learn/glossary.md`,
`### Rung`; `ladder/ladder/rungs.py:261` numbers them in one global sequence).
The port already drops both: `uvx satyrn-pi eval --suite <name>`, and the
[applicability mapping](../rules-applicability.md) maps `ladder/` to the new
eval package.

## What the inventory measured

Counts over the port's own documents on 2026-11-16, excluding the verbatim
`docs/provenance/` copy, which is never edited:

| Term | Occurrences | Now, on the active surface (BRIEF, ROADMAP, README, glossary) |
| --- | --- | --- |
| `stage` | 36 | 1, and it says the concept is not added |
| `remedy unit` | 6 of 36 `unit` | 0 |
| `floor` | 6 | 0 |
| `tier` | 15 | 0 |
| `ladder` / `rung` | 13 / 5 | 2, both contrast or exclusion |
| `screen` / `redispatch` | 23 / 6 | 7 / 2, all explanatory |

The remaining occurrences are in research notes quoting the source, where the
review keeps the original wording with a dated mapping beside it.

## Rejected alternatives

- **Rename every occurrence of Stage to Preset.** This was considered and is
  worse: it invents a label for a list that needs no label, and `preset` already
  means something narrower — the ordered remedy list, not the worker state,
  model, host or suite. Prefer naming the five directly.
- **Replace screen with pilot run.** Renaming does not remove a concept, and the
  source SDD term is already documented. Explain it at first use instead.
- **Replace redispatch with retry.** These are not synonyms: a retry repeats a
  failed request; redispatch sends failures back for further work.
- **Ban the retired words outright.** Ordinary English uses `stage` and `screen`,
  and a quotation of the source must keep its words. A blanket ban produces
  exemptions nobody reads; the check below makes each exemption visible at the
  point of use.
- **Claim one universal industry dictionary.** Frameworks differ: Harbor has
  tasks, datasets, trials, jobs; Inspect combines datasets, solvers and scorers;
  EleutherAI has tasks and groups. Each adopted term needs its local meaning
  written once.

## Then gate it

The gate is two checks, both installed in P2.1, both proved the way the
process-spawning tripwire is proved: a planted violation must fail the suite,
and the tripped case is recorded.

**1. A numeric jargon budget.** The glossary's defined terms are counted, and
the count must not exceed the number P1.2 agrees. Adding a term is a reviewed
decision with a line in the diff; it is never a side effect of a paragraph.

**2. A retired-term check.** A script scans the declared scope and fails on any
retired term. Scope is user-facing documentation — README, BRIEF, ROADMAP,
`docs/*.md` and the site sources. Out of scope by construction: research notes,
`docs/provenance/`, plan and spec records, code paths such as `remedies/`, and
`evals/` record names.

An exemption is declared at the point of use, not in a list elsewhere:

```markdown
<!-- vocabulary: source quotation -->
The source called these "rungs"; see the mapping in rules-applicability.md.
```

The check prints what the reviewer needs to act:

```
docs/getting-started/quickstart.md:42
  "stage" — say Vanilla, Base, Easy, Medium or Hard, or "preset"
  retire: stage → preset | Vanilla…Hard directly
  exempt: <!-- vocabulary: <reason> --> on the same or preceding line
```

Rules the check follows:

- It reads a single table of retired terms and replacements, so the wording can
  change without touching code.
- `remedies/`, `evals/` and `docs/provenance/` are excluded by path, not by a
  per-file edit.
- It never edits a document. It reports.
- It runs in the default suite with no model, no network and no subprocess.
- It fails on a retired term in a *heading* even when the body is exempt, because
  headings are what the site's navigation shows.

The budget and the check are separate failures: an over-budget glossary and a
retired term in a page are different review conversations.

## Tasks

1. P1.2: write `docs/domain.md` (worker and eval responsibilities, import
   direction, shared run meaning) and the five glossary entries plus any retained
   research terms. Walk Vanilla-on-Easy and Base-with-an-empty-preset, and record
   every ambiguity the walk exposes as a glossary change or a budget argument.
2. P1.2: agree the numeric budget with Nicola, Ben and the implementers, and
   record the number and its scope in `docs/glossary.md`. Confirm or refuse the
   Harbor mapping in the same record, term by term.
3. P2.1: add the retired-terms table as data, and the checker with its tests
   shown to fail first — one test per rule above, plus one for the exemption
   comment and one for a heading.
4. P2.1: plant a violation in a scoped page, see the suite fail, then revert it,
   and record the tripped run in the cycle's evidence.
5. P2.1: wire both checks into the default test command beside the cap and
   lifecycle checks, and state in `docs/sdd.md`'s local additions which failures
   block a merge.
6. Onboarding: when P9.1 writes the installer walkthrough, it uses the product
   names only, and the check keeps it that way.

## Verification

- The retired-terms table and the glossary agree: every retired term has a
  replacement, and every replacement is either defined in the glossary or is
  ordinary English.
- The planted violation fails before the table is added and passes after, and
  its exemption form is shown to work.
- `git grep` for each retired term over the declared scope returns only
  exemptions, and each exemption names a reason that fits its page.
- The budget number in `docs/glossary.md` matches the count the checker reports.

## What would falsify this / risks

- A reader who has never seen the source asks what a "preset" is; if the answer
  needs a diagram, the word is carrying more than a list.
- The Harbor mapping fails the P1.2 walk, for example because "verifier" cannot
  be separated from "grader" in the recorded grades. Then the port keeps its own
  words and says why, per term.
- The check produces more exemptions than fixes on the pages it scans. That
  means the budget is wrong or the scope is too wide, not that the pages need
  more exemption comments.
- Budget inflation: two cycles each add a justified term and nobody removes one.
  The reopen condition is a count above the agreed number in two consecutive
  cycles.
