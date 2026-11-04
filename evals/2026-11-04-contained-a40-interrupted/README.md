# Interrupted A40 contained Phase 1 attempt

**Measured:** one Vanilla attempt on the qualified A40 backend; model execution
stalled, grading infrastructure failed, and the Pod was stopped. **Conjecture:**
quality and budget of corrected six-session cohorts; no comparison ran.

| Item | Observed |
| --- | --- |
| GPU | A40, EU-SE-1, $0.59/hour compute |
| Attempt | 20261104T130432Z-easy-fc000f |
| Completion | stalled on foreground Uvicorn; 180.3s open-call cutoff |
| Model execution | 199.338s |
| Model turns / provider requests | 14 / 14 |
| Output tokens | 2,221 |
| Full / uncached context high water | 5,477 / 1,531 tokens |
| Hidden checks | not run to completion; import failed because generated app module was absent |
| Code health | not checked: all three checker binaries hit noexec scratch |
| Runtime identity / cleanup | verified / verified |
| Accepted baseline sessions | 0; batch retained pending review |
| Worker / remedy screen | not started |

The [machine scorecard](scorecard.md) records missing checks as not run (0/4),
not four demonstrated assertion failures. The generated workspace had `main.py`
while the fixed hidden contract imports `app`; the model stall remains observed
and is not erased by the separate infrastructure failure. This cohort used the
original image and must not be mixed into corrected-image comparative rates.

The [dated correction](../../docs/superpowers/research/2026-11-04-contained-a40-study.md)
records the cause, failing-first regression, corrected executable private scratch
policy, stronger qualification gate and new image/proof. Full verification:
223 Python tests, npm640/640, docs caps4/4, lint clean and all27 real-boundary
qualification checks passed. Initial sandbox-limited npm failed to access uv's
cache; the unrestricted full command passed.

The stopped A40 could not restart: three MCP start calls returned insufficient
host GPU capacity. Fresh MCP reads verified both `icrpuerli5mgih` and the old
`adwa2g95zg24vx` EXITED. No background capacity watcher remains. Persistent
storage is retained and still billed; compute is stopped.

[Raw evidence](raw-evidence.json) includes the complete attempt, backend build
and qualification, controller logs and corrected local qualification. The
published archive was downloaded and SHA-256 verified. No raw trace, stdout or
patch is committed here.

## What would falsify this

A mismatched archive hash, missing identity/cleanup evidence or an unsupported
budget total invalidates the corresponding claim.

## Risks

No completed corrected baseline or remedy screen exists. The four hidden checks
are narrower than full Phase1 acceptance. Restarting a stopped Pod depends on
its original host capacity; this setup has not solved that allocation problem.
