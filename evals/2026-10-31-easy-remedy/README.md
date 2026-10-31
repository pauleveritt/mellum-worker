# Easy remedy — figured out on local Q4 (2026-10-31)

Local M3 (Metal, cached Q4, `llama-server`), suite `easy` (Bronze), n=3 serial,
deadline 1800 s, stall 120 s, thinking on, default prompt and tool set. Each arm
is bare plus the named remedies. The full run-by-run reasoning is in the
[campaign note](../../docs/superpowers/research/2026-10-31-easy-remedy-campaign.md);
the `cap-turns` × `ncm` deadlock that started the search is in the
[deadlock note](../../docs/superpowers/research/2026-10-31-cap-ncm-deadlock.md).

## The arms

| arm | pass | note |
|---|---|---|
| bare (baseline) | 1/3 | `evals/baseline/2026-10-30-vanilla-local-m3-q4` |
| acceptance + ncm | 0/3 | 2/3 stalled on a foreground `python main.py` before the gate could fire |
| nonblock + acceptance + ncm | 1/3 | stall gone, all settled; the contract demanded all 4 phases and accepted any anchor as nav |
| **nonblock + fixed acceptance + ncm** | **6/6** | this record — two independent n=3 runs; `table.md` |

## The remedy

- `tool/background-long-commands` — backgrounds the server the worker starts to
  check its work, so it never stalls before settle.
- `mellum-acceptance` — derives the acceptance contract from the spec, **scoped
  to the phase the prompt names** and asserting the **spec-named nav links** as
  real anchors (fixed in `41c9fbd`; was demanding later phases and accepting any
  `<a href>`).
- `mellum-ncm` — re-runs that contract when the worker tries to settle and sends
  it back with the unmet concept until the contract is green.

No turn cap, so no `cap-turns` × `ncm` deadlock. The pass rate is the stack, not
any one piece: drop nonblock and the stall returns (0/3); leave the contract
whole-roadmap and lax-nav and the gate demands the wrong thing (1/3).

Raw `trace.jsonl`, `stdout.txt`, `diff.patch` and the workspaces are stripped;
each rep keeps `run.json`, `layout.json`, `leaked.json`, `prompt.txt`.
