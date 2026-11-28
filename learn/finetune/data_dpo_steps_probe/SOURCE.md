# data_dpo_steps_probe

A probe build from 2026-11-25 (step pairs before the thinking fix), used only to count how many step pairs
the history yields. Never trained on; kept so no training data is lost. Superseded by data_dpo_mix_raw.

Split 2026-11-26 into section files under 45 MB each (`pairs_io.py`), so no file nears GitHub's limit. The rows and their order are unchanged: `read_pairs` returns exactly the old `train.jsonl` (sha256 0ca8e125434687d637d0d813be7a9933367f23f35ca8a52e764e4e528cef3a3d).
