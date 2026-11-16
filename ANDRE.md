# Questions for Andre during flight back

1. Is the glossary.md accurate?
2. It has "Baseline Worker" which I believe we now call "Base".
3. Does it explain "Arm" correctly and list the different types of arms?
4. The `glossary.md` spiraled out of control. It's really long. We should have a concept budget that is enforced.
5. What is `bare` and what is `base` and do we need both concepts?
6. "nothing named Base exists on his main at all"
7. Do we keep ladder and rung?

## From the `andre-integration` review

1. *Single-source suites. Refuse.* I'm worried about this refusal. It means we have suites with requirements in two
   places: the roadmap and the prompt. The roadmap basically isn't used. That will be confusing.


## Is `ladder` / `rung` standard vocabulary? (no)

Neither word is standard for eval harnesses, and each imports the wrong association.
What the field actually says:

| Ours | Standard |
| --- | --- |
| `ladder/` | eval harness, eval suite |
| `rung` | task, instance, difficulty level |
| tier (Easy/Medium/Hard) | difficulty tier — conventional already |
| arm (`vanilla`, `bare`, `worker`, `strip-thinking`) | experimental arm / condition — conventional |
| n runs per arm | repetitions, trials |

- **`ladder` means the model varies, not the task.** The phrase that owns the
  word is *scaling ladder* (a series of model sizes), and on leaderboards it is a
  ranking. Here the model is fixed and the task composes — the opposite axis, so
  an outside reader's first guess is wrong.
- **`rung` carries two things at once.** The glossary gives it as "one stage of
  the ladder" *and* "a single task at a fixed difficulty" (`learn/glossary.md`,
  `### Rung`). In the code the numbering is one global sequence —
  `RUNGS: dict[int, Rung]` with rung 1 = `calculator` (`ladder/ladder/rungs.py:261`)
  and rungs 6–9 = AgentClinic phases (`rescore.py:50`) — while Easy, Medium and
  Hard are `tier`s. Three axes for what are really suite, task and condition.
- **The port already drops both.** `satyrn-pi/ROADMAP.md` P5.1 says
  `uvx satyrn-pi eval --suite <name>`, and `satyrn-pi/docs/rules-applicability.md`
  maps "`ladder/` and its old commands" to the new eval package. So this is
  naming debt in this repo, not something the new one inherits.
- **Why it matters beyond taste.** The docs are read by people who never met us
  (the installer, the next lead). A name they have to learn is a tax on every
  page; a name that misleads is worse than a blank one.

## Proposals for Andre

1. *One progression.* Use Vanilla → Base → Easy → Medium → Hard and retire
   Baseline Worker. Explain what each adds without making users learn a separate
   vocabulary of arms, stages, tiers and configurations.
2. *Keep the machinery out of the vocabulary.* A preset is just the file listing
   the remedies to enable; it does not need to be another concept in the getting
   started explanation. Keep `bare` for internal tests and `rung` for historical
   records.
3. *Two choices are enough.* Users choose what to enable and which suite to run
   it against—for example, Vanilla on the Easy suite. Keep that distinction
   explicit without adding names for every combination.
4. *Enforce a jargon budget.* Make a jargon budget a project rule, checked
   automatically like document caps. New terms must fit within the agreed limit
   and help users make a distinct decision or understand a distinct behaviour;
   merge synonyms or retire redundant terms to make room.
5. *Retire `ladder` and `rung` from anything a user reads.* Keep them only where
   a record already cites them (an `evals/` path or a rung number in a research
   note) and use eval harness/suite, task, arm and difficulty tier everywhere
   else. The same renaming applies to `tier` vs `rung` in the Getting Started
   text, where the two currently mean different axes with no explanation.
