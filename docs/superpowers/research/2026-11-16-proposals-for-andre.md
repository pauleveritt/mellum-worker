# Detailed proposals for Andre

Return to the [review overview](../../../ANDRE.md).

## Open question

1. *Single-source suites. Refuse.* I'm worried about this refusal. It means we have suites with requirements in two
   places: the roadmap and the prompt. The roadmap basically isn't used. That will be confusing.

## Vocabulary for the port

Propose making the naming change during the port, using
[Harbor's core concepts](https://docs.harborframework.com/core-concepts/index)
as the reference for evaluation vocabulary. Use
[Hamel Husain and Shreya Shankar's guidance](https://hamel.dev/blog/posts/evals-faq/whats-a-minimum-viable-evaluation-setup.html)
for the improvement process: inspect evidence, identify failures and build checks.

| What we now say | What we should say | Meaning in the port |
| --- | --- | --- |
| Ladder / eval suite | Dataset | A collection of tasks, such as Easy, Medium or Hard. |
| Rung / coding task | Task | Instructions, a starting environment and verification of the result. |
| Run / repetition, for one task attempt | Trial | One agent's attempt at one task. |
| Run, for the whole evaluation | Job | The collection of trials executed by an evaluation invocation. |
| Grader | Verifier | The component that evaluates the completed work. |
| Trace, for the conversation and actions | Trajectory | The conversation and action history during a task attempt. |
| Agent, sometimes conflated with its model | Agent | The program completing the task: Pi with the selected extensions; its model is separate. |

Keep Vanilla → Base → Easy → Medium → Hard and preset for the remedy list;
qualify Easy as a dataset or preset when needed. A trajectory is the history,
not all timing and diagnostic telemetry. Trials are repetitions, not seeds.

P1.2 should confirm these proposed names and their boundaries. The agreed
`eval --suite` flag and `run.json` filename remain interface decisions; adopting
Harbor words does not silently rename either. Preserve historical paths, IDs
and records. This proposal adopts vocabulary without requiring Harbor itself.

## Proposals for Andre

1. *Adopt Harbor's eval vocabulary.* Use dataset, task, trial, job, verifier and trajectory with the meanings above;
   preserve source paths, record IDs and historical citations.

2. *One progression.* Use Vanilla → Base → Easy → Medium → Hard; retire Baseline Worker and extra labels for the
   progression.

3. *Hide implementation detail.* Explain preset files when needed; keep `bare` and old rung names out of onboarding.

4. *Two choices.* Distinguish what to enable from which dataset to evaluate—for example, Vanilla on the Easy dataset.

5. *Enforce a jargon budget.* Make it a project rule with an automated check, like document caps.

6. *Reserve Base.* Rename the source guide’s worker-free “Base Pi” setup to Vanilla Pi in the port.

7. *Keep ordinary words ordinary.* Drop glossary entries for Learning Center, Track, Lesson and Before and after.

8. *Move authoring vocabulary.* Put workflow terms in contributor guidance and explain extension hooks beside their
   first example.

9. *One remedy.* Merge Remedy and Remedy unit; retain useful distinctions between tools, guards and other behaviours.

10. *One nudge definition.* Define a corrective message once; describe each remedy’s trigger and limit beside it.

11. *Describe the failure.* Prefer plain failure descriptions to “pathology”; distinguish model mistakes from harness
    and test defects.

12. *One main model.* Merge Main agent and Parent model; call the handoff the worker’s report.

13. *Name the programs.* Explain what Pi and the eval command do; reconcile the conflicting definitions of agent.

14. *Trial, job, session.* A trial attempts one task; a job collects trials; a Pi session is the saved conversation.

15. *Readable metrics.* Use Model requests and Elapsed seconds; explain aggregation without implying different suites
    become comparable per prompt.

16. *One scoring guide.* Explain scores together while distinguishing failed tests, tests that never ran, verifier access
    and corrective feedback.

17. *Clear evidence labels.* Explain evidence once; separate experimental strength from backend, citation age and
    provenance.

18. *Techniques belong in lessons.* Explain specialised experiments where used; distinguish removing previous reasoning
    from requesting shorter new reasoning.

19. *Trim AI background.* Keep practical basics; defer training, embeddings and other background until a lesson needs
    them.

20. *Fix misleading links.* Remove Easy/Medium/Hard → Challenge and bare Pi → Vanilla aliases where they obscure the
    intended meaning.

21. *Test the vocabulary contract.* Check the budget and links rather than obsolete headings; allow ordinary words and
    historical citations.

22. *Keep facts with their source.* Put counts, settings, thresholds and results in their owning references; correct
    stale onboarding and phase descriptions in the port.

23. *Prefer familiar, accurate words.* Avoid mechanical substitutions: a preset is a remedy list, and corrective
    feedback differs from retrying a request.

24. *Define the domain early.* Add P1.2 before SDD setup to agree worker/eval responsibilities, shared run meaning,
    vocabulary and jargon budget.

Evidence: [glossary audit](2026-11-16-glossary-audit.md) · [port vocabulary review](../../../satyrn-pi/docs/superpowers/research/2026-11-16-vocabulary-review.md).
