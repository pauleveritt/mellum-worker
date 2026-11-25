# data_dpo_mix_raw

Built 2026-11-25 from the same 182 base-model run folders as `data_dpo_phases_all`,
after `regrade_phases.py` wrote `phase_grades.json` beside each multi-phase run
(52 of 66 verified: the replayed final state grades exactly like the record, so each
phase is graded on its own module instead of the final workspace).

    build_dpo_phases.py --source <each kept runs/ folder> \
      --source-all-phases runs/2026-11-24-mint-satyrn --steps \
      --model .models/Mellum2.1-12B-A2.5B-Thinking-6bit --out data_dpo_mix_raw

Phase pairs (max 60 per phase): medium:p2 46 wins / 10 losses, p3 46 / 9, p4 34 / 17
(valid 6 on p4, held out by trajectory). Step pairs: 117 train, 14 valid (every 10th run):
a failed read/edit/write/ls call against the next call, which succeeded, at the same
context, tool call only. Easy and Medium phase 1 never enter (the Easy screen task).
Train 297, valid 20.
