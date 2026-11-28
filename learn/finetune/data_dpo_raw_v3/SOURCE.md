# data_dpo_raw_v3

Built 2026-11-26 like `data_dpo_raw_v2` (the 92 base-model folders in `../sources_base_runs.txt`,
`--steps --pathologies`), plus:

- our tune's Medium runs `runs/2026-11-26-ours-mix120-medium` (ours-mix120 Q4_K_M, baseline-worker, n=3),
  regraded with `regrade_phases.py` and `--regressions`;
- base and ours-mix120 on the 12 `learn/code/suites/py-features-train` tasks (n=3 each,
  `runs/2026-11-26-pyfeat-train-{base,ours-mix120}`), every phase kept, with `--idioms-root` so a failed run's
  last write of each reference file is paired with the reference. The py-features eval tasks never enter;
- new with `--pathologies`: shell pairs (`:shell`), a bash command that failed on its own shape (quoting, a
  `python -c` that can't parse, a flag this shell lacks) against the clean bash retry that followed.

    ARGS=$(grep -v mint-satyrn sources_base_runs.txt | sed "s#^#--source ../../runs/#" | tr "\n" " ")
    uv run --no-project --with mlx-lm==0.32.2 python build_dpo_phases.py $ARGS \
      --source ../../runs/2026-11-26-ours-mix120-medium --source-all-phases ../../runs/2026-11-24-mint-satyrn \
      --source-all-phases ../../runs/2026-11-26-pyfeat-train-base \
      --source-all-phases ../../runs/2026-11-26-pyfeat-train-ours-mix120 \
      --idioms-root ../code/suites/py-features-train --steps --pathologies \
      --model ../../.models/Mellum2.1-12B-A2.5B-Thinking-6bit --out data_dpo_raw_v3

Build output:

    segments: {'no-grade': 100, 'phase-graded': 59, 'regressed-phases': 8, 'base-path-flag-cleared': 11, 'contaminated-or-no-trace': 20, 'step-ok': 182, 'ok': 258, 'shell-ok': 34, 'unused-ok': 7, 'rejected-never-wrote': 14, 'step-misaligned': 51, 'outside-ok': 6, 'shell-misaligned': 1, 'misaligned': 15, 'unused-misaligned': 1, 'idiom-ok': 8, 'outside-misaligned': 1}
    per phase: {"medium:p2": {"win": 48, "loss": 11, "train_pairs": 60, "valid_pairs": 0, "median_tokens": 11216}, "medium:p3": {"win": 48, "loss": 9, "train_pairs": 60, "valid_pairs": 0, "median_tokens": 21266}, "medium:p4": {"win": 36, "loss": 18, "train_pairs": 60, "valid_pairs": 6, "median_tokens": 25189}, "py3.14-annotations-return:p1": {"win": 5, "loss": 1, "train_pairs": 5, "valid_pairs": 0, "median_tokens": 17956}, "py3.14-annotations-signature:p1": {"win": 2, "loss": 4, "train_pairs": 8, "valid_pairs": 0, "median_tokens": 24258}, "py3.14-tstring-html:p1": {"win": 0, "loss": 5, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 21800}, "py3.14-tstring-shell:p1": {"win": 0, "loss": 6, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 20322}, "py3.14-zstd-bytes:p1": {"win": 2, "loss": 4, "train_pairs": 8, "valid_pairs": 0, "median_tokens": 10840}, "py3.15-frozendict-freeze:p1": {"win": 0, "loss": 5, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 16044}, "py3.15-frozendict-headers:p1": {"win": 0, "loss": 5, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 17282}, "py3.15-lazy-import-plugins:p1": {"win": 1, "loss": 5, "train_pairs": 5, "valid_pairs": 0, "median_tokens": 14510}, "py3.15-sentinel-unknown:p1": {"win": 0, "loss": 6, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 10764}, "py3.15-sentinel-unset:p1": {"win": 0, "loss": 6, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 19717}, "py3.15-typeddict-closed-metrics:p1": {"win": 0, "loss": 6, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 17291}, "py3.15-typeddict-closed-options:p1": {"win": 0, "loss": 6, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 19377}, "satyrn-format_number:p1": {"win": 3, "loss": 0, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 5926}, "satyrn-selfhost-cell-loop:p1": {"win": 0, "loss": 3, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 17386}, "satyrn-selfhost-docs-linter:p1": {"win": 0, "loss": 3, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 23289}, "satyrn-selfhost-guard-prefixes:p1": {"win": 0, "loss": 1, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 27224}, "satyrn-selfhost-review-script:p1": {"win": 3, "loss": 0, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 23212}, "satyrn-selfhost-run-record-gate:p1": {"win": 0, "loss": 3, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 23695}, "satyrn-selfhost-speed-probe:p1": {"win": 0, "loss": 3, "train_pairs": 0, "valid_pairs": 0, "median_tokens": 20144}, "steps": {"train": 209, "valid": 28}}
    train 415  valid 34  -> data_dpo_raw_v3
