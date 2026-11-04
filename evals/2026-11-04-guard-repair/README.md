# Guard repair: remedied Easy Phase 1 repeat screen

Both observed defects are repaired: simple recognized server help/version
queries pass, and native Pi guard refusals count once per tool call. The same
five-remedy n=1 screen then passed its four hidden checks, health and completion.
This is a presence screen, not a success rate or whole-phase acceptance claim.

| Screen | Hidden checks | Health | Completion | Requests | Output tokens | Actual seconds | Peak prompt tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Repaired five remedies | 4/4 | pass | settled | 19 | 9,078 | 39.932 | 13,558 |
| [Earlier five remedies](../2026-11-04-contained-h100/README.md) | 4/4 | pass | settled | 18 | 5,823 | 28.504 | 10,949 |

The repeat used 3,255 more output tokens and one more request. It ran on a
newly qualified H100 host in EU-FR-1, with the same model, pinned backend revision,
serving settings, Pi version and sampling; no causal timing comparison is made.
Mac tools ran inside temporary containment; inference ran only on the Pod GPU.
Collection was sequential, with two configured 50k-context server slots.

The actual repeat loaded all five remedies in order and sent all three prompt
fragments. Every one of its 19 requests sent the 16,384-token output ceiling.
No transport/provider error occurred; output accounting is complete. It first
searched for absent tests, ran pytest against the absent directory, then wrote
one test and reran it successfully. Three ordinary tool errors are retained.
Its own one-test gate is separate from the four hidden checks. It attempted no
server launch/help command; both the actual refusal count and trim-note count
were zero. This trajectory therefore cannot demonstrate a prevented hang or a
real-run trimming effect.

Repair verification is separate and targeted: each regression failed first;
40 guard/remedy tests, three focused accounting tests, and all 641 repository
tests then passed. The rebuilt image passed [27 containment checks](boundary-qualification.json)
and [10 actual-Pi interaction checks](interaction-qualification.json): help and
version queries pass, a genuine foreground start is refused and counted exactly
once, all prompt fragments arrive, and 12,000 characters trim to 8,000 plus note.
The original erroneous run/counter remains unchanged.

[Protocol and outcome](../../docs/superpowers/research/2026-11-04-guard-repair-rerun.md),
[scorecard](remedy-scorecard.md), [run record](run.json),
[behavior and cleanup audit](observations.json), [frozen backend](backend-config.json),
[raw archive provenance](raw-evidence.json).

Pod `dnjioygj7izxh0` stopped immediately on completion and was independently
[read back EXITED](final-pod.json). The controller and SSH tunnel exited; no
owned Docker container or volume remains. Persistent storage remains billable.
The baseline cohorts remain in their original record; this screen establishes
neither individual remedy effects nor a reason to promote the bundle by default.
