# data_dpo_raw_v2

Built 2026-11-26 from the 92 base-model run folders listed in `../sources_base_runs.txt` (the same runs as
`data_dpo_mix_raw`), after `regrade_phases.py --regressions` wrote `phase_regressions.json` beside the 55
verified multi-phase runs.

    bash -c 'ARGS=$(grep -v mint-satyrn sources_base_runs.txt | sed "s#^#--source ../../runs/#" | tr "\n" " ")
      uv run --no-project --with mlx-lm==0.32.2 python build_dpo_phases.py $ARGS \
        --source-all-phases ../../runs/2026-11-24-mint-satyrn --steps --pathologies \
        --model ../../.models/Mellum2.1-12B-A2.5B-Thinking-6bit --out data_dpo_raw_v2'

What is new against `data_dpo_mix_raw` (the pathologies the mix120 screens showed):

- **Earlier-phase regressions:** a phase that broke an earlier phase's checks counts as failed. 7 phases in 5
  runs broke an earlier one; every one of them had already failed its own checks, so no label changed.
- **Outside-workspace searches** (`:outside`): `find /`, `ls ~` and the like against the same command aimed
  at `.`. 1 pair (6 such calls in kept phases; the rest misaligned or were in held-out phase 1).
- **Unused imports** (`:unused`): the last write of a gated source file leaving an import unused, against the
  same write with ruff 0.14.0's F401 fix. 7 pairs.

Both pathology kinds keep the thinking the model wrote and score only the tool call. Phase pairs and step
pairs are built as in `data_dpo_mix_raw`. Easy and Medium phase 1 never enter (the Easy screen task).
Train 305 (180 phase, 117 step, 8 pathology), valid 20.

Split 2026-11-26 into section files under 45 MB each (`pairs_io.py`), so no file nears GitHub's limit. The rows and their order are unchanged: `read_pairs` returns exactly the old `train.jsonl` (sha256 4019ac60505def40bff46d21e00a9aa81fa13c8e9c864e7f54e130eddd0c1e8f).
