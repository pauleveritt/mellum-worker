# data_dpo_mix_tools_v2

Tools round 2, still no new Python knowledge: `data_dpo_raw_v4` cut with
`cut_mix.py --raw data_dpo_raw_v4 --per-phase 10 --steps 40 --no-knowledge`.

Smaller than `data_dpo_mix_tools` on purpose: the first tools tune screened best at update 15 (60 pairs seen) and
regressed on Medium by its final update 66, so this set is about 39 updates for one epoch, with every re-read,
cleanup, shell, outside and unused pair kept so the new failure shapes are a large share of it. Valid copied
unchanged.

    train 155 {'medium:p2': 10, 'medium:p3': 10, 'medium:p4': 10, 'step': 40, 'reread': 29, 'shell': 35, 'cleanup': 7, 'outside': 6, 'unused': 8} -> data_dpo_mix_tools_v2
