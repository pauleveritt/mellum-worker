# data_dpo_raw_v4

Built 2026-11-27 with the same sources and flags as `data_dpo_raw_v3` (see its SOURCE.md), plus the tools tune's
own Medium runs, regraded per phase with `regrade_phases.py` and `--regressions`:

- `runs/2026-11-26-tools-medium` (final tools adapter, n=3): the runs that repeated one failed edit up to 7 times;
- `runs/2026-11-27-tools15-medium` and `runs/2026-11-27-tools15-medium2` (update-15 checkpoint, n=6).

New pair types from the pair builder since v3 (`--pathologies`):

- `:reread`: an edit straight after a failed edit to the same file that failed too, against reading the file;
- `:cleanup`: the final answer of a run that left a scratch `.py` behind, against `rm -f` of those files first;
- `:idiom` now also pairs a last `edit` (replayed from the task's `base/` copy), not only a last `write`.

The Easy suite and the py-features eval tasks never enter.

    NEW="../../runs/2026-11-26-tools-medium ../../runs/2026-11-27-tools15-medium ../../runs/2026-11-27-tools15-medium2"
    for R in $NEW; do uv run --no-project python regrade_phases.py $R; uv run --no-project python regrade_phases.py --regressions $R; done
    ARGS=$(grep -v mint-satyrn sources_base_runs.txt | sed "s#^#--source ../../runs/#" | tr "\n" " ")
    SRC=""; for R in ../../runs/2026-11-26-ours-mix120-medium $NEW; do SRC="$SRC --source $R"; done
    uv run --no-project --with mlx-lm==0.32.2 python build_dpo_phases.py $ARGS $SRC \
      --source-all-phases ../../runs/2026-11-24-mint-satyrn \
      --source-all-phases ../../runs/2026-11-26-pyfeat-train-base --source-all-phases ../../runs/2026-11-26-pyfeat-train-ours-mix120 \
      --idioms-root ../code/suites/py-features-train --steps --pathologies \
      --model ../../.models/Mellum2.1-12B-A2.5B-Thinking-6bit --out data_dpo_raw_v4

Build output:

    segments: {'no-grade': 100, 'phase-graded': 68, 'regressed-phases': 8, 'base-path-flag-cleared': 12, 'contaminated-or-no-trace': 20, 'step-ok': 211, 'ok': 280, 'reread-ok': 30, 'shell-ok': 38, 'unused-ok': 8, 'cleanup-ok': 7, 'rejected-never-wrote': 14, 'step-misaligned': 61, 'reread-misaligned': 19, 'outside-ok': 6, 'shell-misaligned': 4, 'misaligned': 15, 'outside-misaligned': 2, 'unused-misaligned': 1, 'idiom-ok': 53, 'idiom-misaligned': 1}
    train 529  valid 36  -> data_dpo_raw_v4
