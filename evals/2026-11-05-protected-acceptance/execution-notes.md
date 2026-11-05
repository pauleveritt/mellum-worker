# SDD ledger — plan: docs/superpowers/plans/2026-11-04-protected-acceptance.md

Approved: user Proceed after reviewing n=20/arm plan. Base 0c7a05f.
Workspace: existing dedicated paul/initial-fixes branch, clean at start; no
main/master changes. Preserve local evidence and FIXES in this workspace.
Pre-flight: Task1 Gate/package -> Task2 host adapter -> Task3 checker/probes
-> Task4 collection/budget -> Task5 evidence. Interfaces consistent.
Ruling: trusted assertions execute on the host over bounded subprocess probe
observations, not inside the candidate grading process — follows the explicit
candidate/assertion isolation requirement; a malicious application can still
fake behavior, a limitation of finite behavioral acceptance.
Tasks: 1 in progress; 2–5 pending. No inference started.

Task 2: Ruling: actual-Pi exchange qualification depends on the Task3 checker/
probe module, an execution-order dependency absent from the plan — implement
Task3 before declaring Task2 complete. Unit exchange regressions are GREEN;
no incomplete adapter is used to collect runs. Cost: Task2's final gate waits.
Task 1: complete (commits 0c7a05f..8ce564b, tests: uv run --with pytest pytest learn/code/tests/test_acceptance.py -q → 30 passed in 0.06s)

Task2 native preflight: runtime-tamper-green/qualification.json all4 pass.
Initial stdin transport, checker hard timeout and tamper export failures retained
in runs/2026-11-04-protected-acceptance/. Rebuild final image before collection;
preflight image is not the eventual frozen image. No inference server started.
Task 2: complete (commits 8ce564b..4cc5a25, tests: uv run --with pytest pytest learn/code/tests/test_acceptance_containment.py learn/code/tests/test_containment.py -q → 33 passed in 0.48s)

Task3 checker matrix passed at checker-preflight-v3; 28 focused tests pass.
Task4 Ruling: infrastructure integrity failure stops and leaves cohort incomplete,
no replacement in this controller — a broken instrument cannot safely decide;
cost: a later explicit replacement protocol may be needed. Preregistered.
Task4 recovery RED→GREEN: preserve orphan model export before remove, enumerate
control audits, retain interrupted attempt export. Forced native compaction old
image RED/new22acbf GREEN: 4 relay versus3 hooks, completion usage captured.
Full npm identified live menu discovery throwing while unit disabled; focused
regression RED→GREEN, 27 node tests pass; full npm rerun in progress.
Task 3: complete (commits 4cc5a25..7eba3e6, tests: uv run --with pytest pytest learn/code/tests/test_acceptance_checker.py -q → 28 passed in 0.16s)

Fresh reviewer protected_acceptance_final_review (gpt-6-astra/high) reviewed
0c7a05f..7eba3e6. Seven Important findings; all in one consolidated fix pass:
forged pytest report (real-container RED), omitted live recovery (RED), unsafe
launch (RED), unbounded snapshot transport (RED), unequal final audit timing,
variable title false fail (real-container RED), unhashable status (RED).
Fixed pytest post-return observer, live recovery, guardian owns server launch,
absolute snapshot deadline, both arms final-audit before hidden grade using host
remaining, context-variable title probe, typed status. Focused116 pass, real
controller-death dummy-server guardian pass. Final full suite/preparation pending.
Final Ruling: deliberate arbitrary runtime observation forgery is the documented
finite behavioral-test limit; claims do not imply malicious-code attestation —
cost: sophisticated spoofed behavior can pass finite probes.
Final Ruling: kernel/runtime escapes remain outside the approved threat model —
cost: container isolation is not proof against runtime exploits.
Final Ruling: existing hidden grader unchanged per independent-oracle design —
cost: its historical limitations remain, supplemented by external acceptance.
Final Ruling: quality/economics/manual semantic audit awaits collection — no
unmeasured conclusion; cost: no favorable claim before the fixed cohort finishes.
No reviewer Minor findings. Public source push rejected twice by automatic
approval review despite verified user fork ADMIN; no further retry. Local work
continues and explicit publication approval is needed before pushing.
Task 4: complete (commits cba2bb6..e339461, tests: uv run --with pytest pytest learn/code/tests/test_acceptance.py learn/code/tests/test_acceptance_containment.py learn/code/tests/test_acceptance_checker.py learn/code/tests/test_acceptance_budget.py learn/code/tests/test_acceptance_overnight.py learn/code/tests/test_acceptance_pytest_probe.py learn/code/tests/test_containment.py -q → 117 passed in 1.99s)
Final: fixed all7 Important findings in e339461 — focused117 pass; npm665 pass
(includes Python harness suite), docs caps4 pass, site build clean. Actual
forged-tests and valid-variable-title renewed container cases GREEN. Real
abrupt-container recovery retained partial workspace and removed owned resources.
No reviewer Minor findings; no re-review per execution skill. Source publication
blocked by automatic approval review; implementation committed locally only.
Task5 Ruling: manual audit found valid hero-* and site-prefix title false failures
in initial live qualification; stop and retain S1/G1 as no-decision qualification,
correct/qualify public-spec oracle and start a fresh fixed20/arm cohort — trust
requires no known oracle false failure; cost: setup inference retained separately,
not usable for efficacy. S1 also had genuine default-title miss. Operator stop
exposed absent interrupted layout; RED→GREEN host reconstruction. Shutdown proven.
This new measured qualification defect is distinct from the final review pass.
Replacement preparation qualified-batch-v2 GREEN: containment, four valid oracle
variants/all omissions and hostile probes, native pass/repair/exhaust/tamper,
compaction; npm665 and docs/site green. Fresh source1b6fa62, fixed20/arm launched.
Task5 Ruling: second discovered oracle false failure requires replacing CSS-name
whitelist with structural containers, not enumerating more observed class names.
Stop v2 and retain14 as qualification, audit prior artifacts then start fresh v3
20/arm — public spec never required those CSS names; cost: additional setup time
and no efficacy reuse of previous inference. Titles head-block valid RED too;
probe now handles head overrides and rejects body-only title insertion.
V3 source444ec7a/image189f508 preparation GREEN: eight valid variants, all
omissions and hostile candidates, actual Pi interaction and compaction. Sixteen
saved artifacts independently audited without mutation/outcome reuse; no further
markup false failures. Full npm665, focused121, docs caps/site GREEN. Fresh fixed
20/arm collection started under qualified-batch-v3; no raw uploads/public push.

Task5 fixed v3 cohort complete40/40: S1/20 usable, G11/20; both hidden80/80,
health19/20. G29 repairs,12 accepted; one accepted health fail. G12 deadline
90requests/89 complete timings, total output unknown, compaction3442 captured.
S484 requests/203948 output; G841 requests/output unknown; joint no-decision.
Independent post-identity verification:237 ownership records, no remaining owned
containers/volumes/server/controller, listener8002 empty, guardian stopped, zero
freeze drift. All40 home templates source/text audited; semantic proxies and
G17 test typing failure remain explicit. Source publication still blocked; raw
held. Final docs/tests/package verification follows.
Task 5: complete (commits e339461..444ec7a, tests: npm test → ℹ duration_ms 112347.129167)

Task5 close: focused121 GREEN, npm665/665 GREEN, caps4/4 GREEN, site clean.
Plan archived with Result; resolved freeze-the-oracle backlog entry removed;
pathology23 records invented oracle constraints, and pathology8 retains the
failed timeout wrapper. Changelog reconciled against this cycle’s commits.
Final branch kept local because public source push requires explicit approval;
no merge, PR or raw upload attempted.
