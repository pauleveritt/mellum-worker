# data_dpo_mix_tools

Tools first: `data_dpo_raw_v3` cut with `cut_mix.py --raw data_dpo_raw_v3 --per-phase 20 --steps 1000
--no-knowledge`. Medium p2/p3/p4 at 20 each round-robin over distinct losing runs, every step pair, and every
outside, unused and shell pair. No idiom pairs and no training-task pass-against-fail pairs, so this tune
shows whether tool calling improves before any new Python knowledge is added. Valid copied unchanged.

    train 262 {'medium:p2': 20, 'step': 158, 'shell': 31, 'outside': 6, 'medium:p3': 20, 'medium:p4': 20, 'unused': 7} -> data_dpo_mix_tools
