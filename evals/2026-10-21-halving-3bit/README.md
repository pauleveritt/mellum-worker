# 2026-10-21: halving Mellum to 3-bit — how far does a cheaper worker get?

**What is measured.** The 6-bit Mellum re-quantized to 3-bit
(`scripts/halve-model.sh`, 3.502 bits/weight, 5.0 G vs 9.2 G), run on ladder
rungs 1-8, direct mode, `tuned`, guards on, native tool-calling, n=1, **no
mediation**. Result (`table.md`): **3/8** — passes the simple single-file
coding rungs (1-3), fails the harder multi-file rungs (4-5) and the AgentClinic
rungs (6-8).

**Takeaway.** Halving to 3-bit keeps trivial single-file fixes and loses
everything harder; the bits are load-bearing past a one-spot edit. The 3-bit is
faster per token (~133 vs ~112 tok/s) and lighter (~5 G wired vs ~9 G) but the
speed is eaten by flailing on the rungs it can't do (rung 8 = 600 s).

**Caveats.**
- **Lossy-on-lossy:** the 3-bit was re-quantized from the 6-bit (dequantize →
  3-bit), not converted from source, so some damage is the double-quant.
- **Rungs 6-8 un-mediated:** no frozen test placed, so v7 ghost-hunts as in
  shipped Mode; those fails are confounded. The clean signal is rungs 1-5.
- **n=1.**

Note: [`research/2026-10-21-halving-3bit.md`](../../superpowers/research/2026-10-21-halving-3bit.md).
Raw `trace.jsonl`/`stdout.txt`/`diff.patch` stripped (`AGENTS.md`).
