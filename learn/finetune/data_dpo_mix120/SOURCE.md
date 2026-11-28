# data_dpo_mix120

`data_dpo_mix_raw` cut to a 50/50 mix of phase pairs and step pairs, 120 train pairs:
medium:p2 20, p3 20, p4 20 (round-robin over distinct rejected runs: 10, 9 and 14
losers), and 60 step pairs (random, seed 0). Valid copied unchanged (6 phase + 14 step).
The cut keeps training to about 30 updates (accum 4).

Rebuilt 2026-11-25 18:50: step pairs now keep the thinking the model wrote before the failed call on both
sides (the model thinks on every turn: 1388 of 1388 recorded turns), and only the tool call is scored
(`scored_span(calls_only=True)`). Tool-call arguments keep non-ASCII as the chat template does.
