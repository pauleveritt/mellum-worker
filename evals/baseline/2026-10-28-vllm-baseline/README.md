# vLLM baseline, 2026-10-28

Vanilla Pi (no extensions, skills, prompt templates or context files; the
recorder only) driving Mellum 2.1 BF16 on vLLM 0.32.0, on one RTX A6000
(vast.ai instance 58114859), with Pi 1.3.0 on an Apple M3 client over an SSH
tunnel. Pins: `scripts/baseline/pins.env`; recipe: `scripts/baseline/README.md`;
reading: `docs/superpowers/research/2026-10-28-vllm-baseline.md`.

- `manifest.json`: the commit, every pin, the server and GPU read live, the
  client. `suites_run` records the suites' rerun (commit `bd416f0`, stall 120 s).
- `ladder/`: rungs 1–12, n = 3, `--mode primary --plain`, 600 s deadline
  (commit `6264a2b`): `table.md` and each run's `run.json` and `final.md`.
- `suites/`: Bronze, Silver and Gold (`easy`, `medium`, `hard`), n = 3, `bare`
  arm, `--grade`, 2,700 s deadline, 120 s stall cutoff: each session's
  `run.json`, `stalled.json` where the cutoff fired, and `suites.txt`.

Raw traces, stdout and diffs are not in git. A first suites attempt without
the stall cutoff was stopped by hand after a 45-minute hang and is not part of
this record.
