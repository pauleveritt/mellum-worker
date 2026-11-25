# data_dpo_phases_all5

`data_dpo_phases_all` with Phases 2 and 3 capped at 5 train pairs each (each has a
single loser, so every pair repeats the same rejected run); Phase 4 kept in full.
Train 70 (medium:p2 5, medium:p3 5, medium:p4 60), valid 6 (copied unchanged).
The cap keeps the first 5 rows per phase of the builder's shuffled train.jsonl.

Trained 2026-11-25: `dpo_native_train.py --data data_dpo_phases_all5 --beta 10 --lr 2e-5
--accum 4 --step 2048 --epochs 1` on .models/Mellum2.1-12B-A2.5B-Thinking-6bit.
