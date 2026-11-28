# What goes into the 1.5B's distillation

The single record of every source that feeds the student's training data, so any future run can be rebuilt or
extended. Add a row for every teacher batch before its data is used. Decisions: docs/adr/0005, 0009, 0010.

## Teacher

- **Model:** Mellum 2.1 (`/models/mellum`), served by vLLM on the lab box `nvidia-rtx4500` (192.168.88.99),
  reached at `http://192.168.88.99:11490/mellum/v1` (vLLM flags: `--reasoning-parser qwen3`,
  `--tool-call-parser hermes`, `--max-model-len 65536`, `--max-num-seqs 16`, fp8 KV cache).
- **Harness profile:** `learn/code/profile-lab` (same sampling as the llama.cpp Mellum profile: temperature 1.0,
  top-p 0.95, top-k 20).
- **Harness shape** (the student's inference shape, ADR 0009): `--arm vanilla --remedy
  "preset:baseline-worker,context/trim-tool-output,context/narrow-tools,prompt/think-briefly"`.

## Held out from all training

The AgentClinic family (`easy`, `medium`, `hard`, and Satyrn's `agentclinic-*`), the Python eval tasks
(`suites/py-features`), and every public benchmark (BFCL, EvalPlus, Aider).

## Training tasks

| Source | Tasks | Notes |
|---|---|---|
| `suites/py-features-train` | 12 | Python 3.14/3.15 features; the teacher lacks some APIs, so many runs fail but their successful calls still count |
| Satyrn self-host + `format_number` | 8 | converted with `satyrn_suites.py`; read locally, nothing goes back to Satyrn |
| New varied suites | to write | small apps and libraries, never AgentClinic, each checked both ways before use |

## Teacher batches

| Date | Run folder | Tasks | Repeats | Shape | Result |
|---|---|---|---|---|---|
| 2026-11-28 | `runs/2026-11-28-teacher-smoke` | py3.14-zstd-bytes | 1 | as above | plumbing check: 19 requests, 17 calls, 2 errors; task failed (API unknown to the teacher) |

## Data sets built from it

| Set | Status | Notes |
|---|---|---|
| `data_sft_v1` | **superseded** | tool results cut to 400 + 200 characters, unlike inference: 31% of examples act on a result seen only in part; also mostly AgentClinic (2,865 of 3,208), now held out |
