# Baselines and remedies audit: what we can trust on 2026-11-05

An audit of the evidence behind the three things the project needs before
it picks the next remedies: a Vanilla Pi floor, a Baseline Worker, and a set
of remedy units that earn their keep. Read with [`AGENTS.md`](../../../AGENTS.md)
(the floor is Vanilla + recorder; the worker bundles nothing; presets are the
result of measurement) and the LC.31–LC.38 rows in
[`ROADMAP.md`](../../../ROADMAP.md).

**What is measured.** Every number below is quoted from a record under
`evals/` or a dated research note, with its n and backend. The file and
commit facts (preset contents, deleted units, stale comments) were read from
the tree at `d83c07b`.

**What is conjecture.** The verdicts "not trusted" are judgements against the
project's own rules (preregistered, n ≥ 3 per arm, same suite, same scoring,
same backend), not new measurements. The proposed tranche in §5 is a set of
hypotheses with no run behind any of them.

## 1. The current rig, so the comparisons are honest

The acceptance work (LC.34–LC.38) runs on one rig: local M5 Max, llama.cpp
`11669/620d2225c`, Mellum `Q4_K_M`, Pi 1.4.0, the contained image, one Easy
Phase 1 task repeated, 600 s task deadline, 180 s tool cutoff, two repairs.
It scores on the **usable** rule: hidden checks **and** code health **and**
settled **and** layout **and** the operator-supplied external acceptance
package. Hidden checks alone no longer separate arms: in LC.34 the selective
arm passed hidden 20/20 and was usable 1/20
([record](../../../evals/2026-11-05-protected-acceptance/README.md)).

Everything measured before 2026-11-04 is on a different backend, a different
scoring rule, or both.

## 2. Vanilla Pi: no floor on the current rig

| Cohort | Rig | n | Hidden all-pass | Usable / joint | Status in its own words |
| --- | --- | ---: | ---: | ---: | --- |
| [LC.31 native reference](../../../evals/2026-11-03-vanilla-easy/README.md) | Runpod PRO 4500, Pi on the Mac, not contained | 6 | 4/6 | pass-and-settled 1/6 | isolation withdrawn ([analysis](2026-11-03-baseline-deep-analysis.md)); LC.33: "new shared contained Vanilla reference required" |
| [Contained H100](../../../evals/2026-11-04-contained-h100/README.md) | Runpod H100, contained | 6 | 2/6 | joint 0/6 | "historical reference" ([layout3](2026-11-04-local-layout3.md)); no roadmap row |
| October `bare` screens | A6000, M3, oMLX, vLLM | 3 each | 0/3 – 2/3 | — | each note: "a lead, not a rate" |
| Local M5 Max, usable rule | the current rig | **0** | — | — | **never run** |

Every November cohort on the current rig (LC.34–LC.38) starts from Vanilla
plus five remedies. There is no Vanilla-only arm beneath them, so none of
their counts has a floor to be compared with.

**Missing:** one registered Vanilla + recorder arm, n = 6, on the current rig,
scored on the usable rule and the same acceptance package, with
relay-reconciled budgets (the compaction gap in
[`BACKLOG.md`](../../../BACKLOG.md#whole-session-compaction-accounting)).

## 3. Baseline Worker: three referents and no measurement

"Baseline Worker" currently names three different things:

- **`--arm worker`**, the thin extension: mode machinery, the pre-marker
  history drop and the run record. Nothing else since `fdc6be2` (2026-11-02).
  `FIXES.md` (2026-11-03) says this is what Baseline Worker means.
- **`preset:baseline-worker`**: `narrow-tools`, `repeat-loops`, `empty-turn`,
  `foreground-server`, `outside-workspace`. The thin-worker plan defined it as
  the units that equal the old bundle, but the old bundle also swapped the
  prompt (removed from the worker in `fdc6be2`, no prompt unit added) and
  injected project facts (`context/add-project-facts` deleted in `444da8b`). The
  preset is the old bundle minus its two largest parts.
- **`scripts/product.sh`**: its header says "guards + facts + the 7-tool set"
  but it runs `--mode mode` with no preset, so it runs the thin worker alone.

The equivalence the plan required was never shown. The parity run in
[the thin-worker plan](../plans/2026-10-31-thin-worker.md) was not run; the
request-equivalence test was deleted in `444da8b`; the surviving guard-decision
test's comment, `CHANGELOG.md`'s "a parity test proves it", and the
`run_ladder` "always loads the guard extension" comment are stale. The one
measurement of the preset points the other way: Easy, local Q4, n = 3,
`preset:baseline-worker` **0/3** against the full old worker 2/3
([easy ladder](2026-11-02-easy-ladder.md)).

The thin worker against Vanilla, same rig and n = 6 each, has run twice:

| Cohort | Worker hidden / joint | Vanilla hidden / joint | Note's own reading |
| --- | ---: | ---: | --- |
| [LC.32 native](../../../evals/2026-11-03-worker-easy/README.md) | 5/6 / 0/6 | 4/6 / 1/6 | descriptive only; isolation later withdrawn |
| [Contained H100](../../../evals/2026-11-04-contained-h100/README.md) | 4/6 / 1/6 | 2/6 / 0/6 | "unestablished: a causal Worker benefit"; initial payloads identical across arms |

Neither is on the current rig or the usable rule. Nothing has measured
`preset:baseline-worker` since the 0/3.

## 4. Remedies: which earn their keep

Twenty-one units exist. None has a controlled add-one win from Vanilla at
n ≥ 6 under the usable rule. The evidence, condensed from each unit's header
and the notes it cites:

| Unit | Best evidence | Reading |
| --- | --- | --- |
| `prompt/verify-the-spec` | easy ladder n = 6: 5/6 → 6/6, hidden only, original wording appended to every message | lead; current once-per-task wording (`7b70d09`, `c2cee59`) unmeasured |
| `prompt/name-the-layout` | easy ladder n = 3: fail → 2/3; controlled6 n = 6 joint 3/6 | lead; delivery changed after the ladder (`f6d511e`) |
| `prompt/python-developer` | easy ladder: 2/3 → 3/3, then 4/6 | lead |
| `guard/foreground-server` | stalls 2/3 → 0/3 at n = 3; fired 0× in the 6/6 rung; guard-only3 0/3 usable | hang win, pass neutral; qualified only |
| `guard/foreground-log-follow` | LC.38: zero attempts in the cohort; fake-provider qualification only | qualified only |
| `tool/background-long-commands` | stalls 2/3 → 0/3, oracle 1/3 = 1/3 | hang win, pass neutral |
| `check/external-acceptance` | LC.34 n = 20 + 20: selective 1/20 → gated 11/20 usable; LC.35 0/20 → 10/20 | the one large effect; a unit over host harness and an operator-supplied oracle; both runs `no_decision` at the 18/20 bar |
| `guard/repeat-loops`, `nudge/empty-turn`, `context/use-short-prompt` | fired 0×; null on the suites; 2/3 = 2/3 | neutral |
| `context/narrow-tools`, `guard/outside-workspace`, `guard/turn-cap`, `guard/whole-file-rewrite`, `context/trim-tool-output`, `context/repair-think-tags`, `prompt/concept-sketch`, `tool/keep-a-plan`, `tool/lookup-library-docs`, `check/code-quality`, `workflow/spec-driven-flow`, `delegate/collapse-handoffs` | header says unmeasured, or n = 1 | unmeasured |

Presets against the rule that they are the result of measurement:

- `easy.json` was set from the add-one ladder (n = 6 on its last three rungs,
  hidden checks only, old prompt wording). The ladder's own note says the
  guard "fired 0×, the lever is the verify prompt". The
  [leave-one-out](2026-11-03-easy-leave-one-out.md) registered to check it
  reads "Result: pending the run". Under the usable rule this stack plus trim
  was usable 1/20 and 0/20.
- `medium.json` and `hard.json` are byte-identical to `easy.json`
  (`c4ae905`), with no medium or hard run behind them.
- `baseline-worker.json` is asserted, not measured (§3).

No unit names a suite file, route or value; the suite-specific content lives in
the operator's acceptance package, outside the unit, by design. That is also
why the gate's effect is not evidence for a generic remedy yet.

## 5. Failure shapes with no unit, and the tranche they suggest

From [`learn/pathologies.md`](../../../learn/pathologies.md) and LC.34–LC.38,
in the order the records show them costing the most:

1. **Protected-input edits before execution.** LC.38 G1 edited
   `pyproject.toml`; only the gate caught it afterwards and the candidate
   became ungradable. `outside-workspace` covers searches, not writes.
2. **Dismissing an observed runtime failure.** LC.36 G6 and LC.38 G6 received
   the real startup warning and kept reasoning the code should work.
3. **Startup verification by improvisation.** `uvicorn.run(reload=True)`,
   timeout-wrapped launches left open, log followers: three guards now refuse
   three shapes of the same need, and the model has no affordance that
   answers it.
4. **Placeholder content passing structural checks.** "A short welcoming
   paragraph." appeared literally twice.
5. **Compaction as a correlate of failure.** Every compaction in LC.36–LC.38
   was in a task that failed. Correlation only.

Pi 1.4.0 hooks the remedies do not yet use: `input`, `context_with_system`,
`after_provider_response`, `before_provider_headers`, `pi.appendEntry`,
`pi.exec`. The `input` hook is the mechanism the backlog entry
"A unit that shapes the task in a session" waits for.

The tranche this audit suggests, cheapest and most load-bearing first. Each
is a hypothesis until run:

- **T0, the floor.** Vanilla + recorder, n = 6, current rig, usable rule.
  Without it nothing in LC.34–LC.38 has a baseline.
- **T1, the wrapper.** `--arm worker` alone, n = 6, same rig and rule. A
  presence check that the mode machinery is inert, and the referent for
  "Baseline Worker" if the project keeps `FIXES.md`'s definition.
- **T2, the gate alone.** Vanilla + `check/external-acceptance`, no prompt
  units, n = 6. The decisive missing arm: LC.34 compared S against S + G, so
  no run says how much of 11/20 the five prompt and guard units contributed.
- **T3, leave-one-out on the easy stack under the usable rule**, only if T2
  leaves room for the prompts to matter.
- **T4, new units for shapes 1–3**, as harness guarantees rather than prose:
  a write guard over an operator-declared protected set (shape 1, the same
  boundary the acceptance package already draws); a bounded start-and-probe
  tool that returns readiness, exit status, the first log lines and cleanup
  confirmation (shape 3, replacing three refusals with one affordance);
  feedback that quotes the runtime failure back as a required repair rather
  than a hint (shape 2). Each measured add-one against T2's arm.
- **Housekeeping, no run needed:** correct the stale claims in
  `scripts/product.sh`, `CHANGELOG.md` and the two test and ladder comments;
  record the contained H100 cohort in a roadmap row or retire it; decide the
  Baseline Worker referent in one place.

Semantic acceptance (shape 4) is investigated separately and never as suite
answers in a unit, per `AGENTS.md`.

## What would falsify this

- A record under `evals/` of a Vanilla-only or `--arm worker` cohort on the
  M5 Max freeze scored on the usable rule. Then §2 and §3 are wrong and the
  tranche loses T0 or T1.
- A recorded leave-one-out or add-one on the current prompt wording under the
  usable rule. Then the easy preset is backed and §4 is wrong about it.
- A run where Vanilla + gate alone is usable at the gated arm's level. Then
  the prompt units are not earning their keep and T3 is dropped.
- A run where Vanilla + gate alone is usable at the selective arm's level.
  Then the prompts carry the effect and T4 should wait on T3.

## Risks

- One task repeated six times is still one task; a floor on Easy Phase 1
  says nothing about medium or hard, whose presets are copies of easy.
- The usable rule depends on an operator-supplied acceptance package. A floor
  measured against it is a floor against that package's version; the package
  changed twice during qualification.
- Cohorts of six at the observed rates separate only large effects. T2 is
  worth running because the effect it probes (1/20 against 11/20) is large;
  T3 may not be decidable at n = 6.
- Budgets before the compaction-accounting fix are not whole-session; any
  per-usable cost in the tranche must use the relay-reconciled numbers.
