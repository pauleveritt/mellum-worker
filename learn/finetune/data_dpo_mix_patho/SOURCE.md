# data_dpo_mix_patho

`data_dpo_raw_v3` cut with `cut_mix.py --raw data_dpo_raw_v3 --per-phase 20 --steps 60`: medium p2/p3/p4 at 20
each round-robin over distinct losing runs, 60 step pairs (seed 0), each training task's pairs capped at 20, and
every pathology, shell and idiom pair. Kept for the knowledge round after the tools tune. Valid copied unchanged.

    train 197 {'step': 60, 'medium:p2': 20, 'medium:p4': 20, 'shell': 31, 'medium:p3': 20, 'unused': 7, 'py3.15-lazy-import-plugins:p1': 5, 'outside': 6, 'py3.14-annotations-signature:p1': 8, 'py3.14-zstd-bytes:p1': 8, 'py3.14-annotations-return:p1': 5, 'idiom': 7} -> data_dpo_mix_patho
