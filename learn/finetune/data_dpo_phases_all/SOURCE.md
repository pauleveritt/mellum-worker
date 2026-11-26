# data_dpo_phases_all

Per-phase DPO pairs mined from every base-model harness run in `runs/` (182 folders),
built 2026-11-25 with `build_dpo_phases.py`. Runs made by other models are left out:
any folder whose name holds `sft`, `tuned`, `dpo`, `onpolicy`, `2bit`, `canary`, plus
`mint-satyrn`, which goes in through `--source-all-phases` instead.

    build_dpo_phases.py --source <each kept runs/ folder> \
      --source-all-phases runs/2026-11-24-mint-satyrn \
      --model .models/Mellum2.1-12B-A2.5B-Thinking-6bit --out data_dpo_phases_all

Result: train 154, valid 6 (held out by trajectory on medium:p4).
Per phase: medium:p2 47 wins / 1 loss, medium:p3 47 / 1, medium:p4 32 / 14; satyrn all-pass or all-fail (0 pairs).
Token ids are for the Mellum2.1-12B-A2.5B-Thinking tokenizer.

Split 2026-11-26 into section files under 45 MB each (`pairs_io.py`), so no file nears GitHub's limit. The rows and their order are unchanged: `read_pairs` returns exactly the old `train.jsonl` (sha256 1d2d8dc4bdc806f908bdabc5267a2161dc57b8f28038a698f32ad9fd3c316656).
