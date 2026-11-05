# LC.39 rig qualification on the Mac (uncounted)

Plan Task 11. No model session ran and nothing here is counted.

**The native path qualified against a scripted fake server.** Four cases drove the real
driver path: budget proxy, pinned Pi 1.4.0, native session, sweep, reconciliation and
grading ([`fake-provider.json`](fake-provider.json), per-case records in `cases/`).

| Case | Expected | Observed |
| --- | --- | --- |
| Budget | session ends `budget`, counted | 3 requests served, the 4th refused; `budget`, counted |
| Stream reset | unknown usage charged 16,384, never zero | one `usage` row, `outputTokens: null`, charged 16,384 |
| Direct server call | session invalid by reconciliation | invalid: server generations do not reconcile with proxy requests |
| Detached `setsid` listener | swept, port closed | swept 1, port no longer listening |

**Host M failed conformance on numerics** ([`host-card-M.json`](host-card-M.json)). Eight
items passed: allowlist, identity with the pinned server flags, capacity at 42,658 prompt
tokens per slot, protocol, throughput, stability, tooling and isolation (uncontained).
`llama-perplexity` at b11669 on Metal returned a finite first chunk (14.46) and NaN for
every later chunk, so it printed no estimate.

Manual probes on the same build and weights, `docs/sdd.md`, `-c 1024`:

| Setting | Result |
| --- | --- |
| Metal, default batch | NaN |
| Metal, `-b 256 -ub 256`, `-ub 64`, `-b 1024` | NaN |
| Metal, `--swa-full`, and `-fa off` | NaN |
| CPU only, `-ngl 0` | finite, PPL 27.63 ± 3.53 |

So the defect is in the Metal path of the tool's all-positions logits, for this
sliding-window MoE model at this build. Whether the server's generation path is affected
is **not measured**. Its protocol items pass, and the LC.34–LC.38 Metal cohorts wrote
coherent code. Under the design, a host that fails conformance contributes no counted
session, so host M is excluded until this is resolved.

Commit at qualification: see `fake-provider.json` (`commit`) and `host-card-M.json`.
Pins digest in both. Raw traces stay in `runs/` and are not published.
