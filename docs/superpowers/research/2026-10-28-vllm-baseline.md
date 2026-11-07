# A replicable vLLM baseline for Mellum 2.1

**What is measured.** The baseline ran on 2026-10-28: ladder rungs 1–12 and
the Bronze, Silver and Gold suites, n = 3 each (results below), after screen 1
(n = 1). Checked the same day:
vLLM v0.32.0 lists `MellumForCausalLM` (served through its Transformers MoE
backend since vLLM PR 59679); vLLM's recipe and JetBrains' model card serve it
with `--reasoning-parser qwen3` and `--tool-call-parser hermes`; the 2.1 chat
template honours `enable_thinking: false`; the pinned image is built on CUDA
13.0 (driver 580+). `baseline.py client` installed the pinned Node (checksum
verified) and Pi 1.3.0 on macOS arm64, and `baseline.py offers` returned three
verified on-demand RTX A6000 offers at $0.40–0.48/h with drivers 580 and 595.

**What is conjecture.** Any rate: three sessions say what happens, not how
often. That results are stable enough across hosts and client machines of the
pinned kind to call a run elsewhere a replicate.

## Why a new baseline

Every ladder number so far was measured on Apple Silicon (oMLX, MLX 6-bit;
some llama.cpp `Q4_K_M`). Nobody without that Mac and that server build can
rerun them. The new baseline is for anyone to rebuild from one command, on
macOS, Linux or Windows (WSL2 for the run step).

It measures **Pi and the model, nothing else**: vanilla Pi with no plugins,
extensions, skills, prompt templates or context files, on every ladder rung
(`run_ladder --mode primary --plain`) and every eval suite (the `bare` arm).
The recorder is loaded as the measuring instrument; its handlers return
nothing, so Pi's requests are unchanged. Every later change, the worker
included, is measured against this.

It runs **the model at full precision (BF16) through vLLM**, not the
shipped 6-bit product. vLLM has no 6-bit format, and its parsers return
structured tool calls and reasoning where oMLX and llama.cpp pass raw text.
So it starts a new table: a gap against the Apple-Silicon records is a
server-and-precision finding, not a regression.

## Where things run

vLLM runs on a rented GPU; Pi, the ladder and the suites run on the
operator's machine, through an SSH tunnel to the box. The GPU is the only thing
worth renting, and the budget is about $0.50/h. The cost is that network
latency and the client's CPU enter wall time; the manifest records the client
so a reader can see it.

## The pins

All of them live in [`scripts/baseline/pins.env`](../../../scripts/baseline/pins.env);
[`baseline.py`](../../../scripts/baseline/baseline.py) and the box scripts read
nothing else. The [recipe](../../../scripts/baseline/README.md) is how to run it.

| What | Pin |
| --- | --- |
| GPU | 1× NVIDIA RTX A6000, 48 GB (49140 MiB), driver ≥ 580; checked on the box and again before the run |
| Server | vLLM 0.32.0, image by digest |
| Model | `JetBrains/Mellum2.1-12B-A2.5B-Thinking` @ `92ddae9f`, BF16 |
| Serving | max-model-len 131072, gpu-memory-utilization 0.90, seed 0, qwen3 reasoning, hermes tools |
| Client | Node 22.19.0 (SHA-256 per platform), Pi 1.3.0 (the newest the ladder has recorded runs on), vastai 1.9.1, the ladder's and root `uv.lock` |
| Pi profile | vLLM provider, temperature 1.0, top-p 0.95, top-k 20, 16,384 output tokens (the model card's defaults and the suites' existing profile) |
| Run | ladder rungs 1–12 and suites easy/medium/hard, n = 3 each; deadlines 600 s (ladder) and 2,700 s (suites) |

Why the RTX A6000: BF16 weights are 24.3 GB (vLLM's recipe says 29 GB
minimum), which rules out 24 GB cards. Of the cards with room near
$0.50/h, the A6000 is a standard workstation part with native BF16 and several
verified offers. V100s are cheaper but have no BF16, which would change the
numerics. The 48 GB "4090" is a modified card nobody can count on renting. An
H100 SXM was the first pick, but the only one with a new enough driver cost
$4.19/h.

## Screen 1 (2026-10-28)

Record: [`evals/2026-10-28-vllm-screen1/`](../../ladder/2026-10-28-vllm-screen1/)
(manifest, ladder table and `run.json`s, the suite's `run.json`; raw traces
stripped). Box: vast.ai instance 58114859, RTX A6000 (49140 MiB, driver
595.104.02), $0.402/h; client: an Apple M3 laptop over the SSH tunnel.

| Session | Result | Requests | Wall | What happened |
| --- | --- | --- | --- | --- |
| Ladder rung 1 (plain) | pass | 11 | 33.8 s | built and stopped |
| Ladder rung 6 (plain) | FAIL, deadline | 20 | 600 s | ran `python app.py`, which serves forever, and waited |
| Easy suite (bare) | FAIL, checks did not run | 20 | 46.9 s | wrote `main.py` instead of the layout's `app.py` and stopped without testing |

An earlier easy session in the same screen (stopped by hand, not recorded)
ran `uvicorn app:app --reload` in the foreground and waited too.

The presence questions:

1. **Box and server — yes.** The pinned GPU passed the box check; vLLM 0.32.0
   started with 131,072 tokens of context, with 18.9 GiB of KV cache left
   (1.27 M tokens; 9.7 concurrent full-length requests). Start to serving took
   about 6 minutes: 264 s downloading weights from Hugging Face, 7 s loading,
   56 s engine warm-up.
2. **Pi over the tunnel — yes.** Tool calls arrived as tool calls and thinking
   as reasoning (rung 1 passed; the live trace showed both). Single-request
   generation ran at roughly 75–110 tokens/s.
3. **Records — yes.** `manifest.json` carries the server, the box's GPU and the
   client; each ladder `run.json` carries the server and the Pi version. Its
   `gpu` field is empty because the client has no GPU; the manifest is where
   the box's GPU lives.
4. **Wall.** A session that works takes under a minute here; a session that
   starts a foreground server costs its whole deadline.

What the screen shows about vanilla Pi, at n = 1: the foreground-server
pathology appeared in two of the three sessions, and Pi has no default bash
timeout to end it, so the deadline does. That is a baseline result, not a
harness fault, and it is what later arms are measured against.

Harness faults found and fixed on the way: `--mode primary` ignored
`--model` (rungs failed in 0.2 s), the ladder got an unrewritten profile, the
tunnel shared port 8000 with the apps the model writes (now 18000),
`watch_ladder.py` was too slow to print on macOS, and `all` had no way to keep
the box (now `--keep`).

After the screen the suites gained a pinned stall cutoff (one tool call open
120 s ends the session as stalled, Pi untouched): at a 2,700 s deadline a
single hung server cost 45 minutes.

## The baseline (2026-10-28)

Record: [`evals/baseline/2026-10-28-vllm-baseline/`](../../ladder/2026-10-28-vllm-baseline/).
The ladder ran at commit `6264a2b`; the suites were rerun at `bd416f0` with the
stall cutoff, after a first attempt hung on a server for 45 minutes and was
stopped by hand. The reading was not preregistered; the pins were fixed before
the run.

| Instrument | Level | Passes | Mean wall | What failed |
| --- | --- | --- | --- | --- |
| Ladder | rungs 1–4 | **12/12** | 13–80 s | nothing |
| Ladder | rung 5 | **2/3** | 87–150 s | one stopped with the work incomplete |
| Ladder | rungs 6–9 | **4/12** | up to 600 s | foreground servers to the deadline (rung 6 all three), early stops |
| Ladder | rungs 10–12 | **8/9** | 67–220 s, two at 600 s | a rung 10 deadline; a rung 11 pass also ran to its deadline after finishing |
| Suites | Bronze | **1/3** | 53 s | one wrote `main.py` (checks could not run); one stalled on `uvicorn` |
| Suites | Silver | **1/3** | 337 s | one missed 14 of 18; one passed all 18 checks and failed the quality gate |
| Suites | Gold | **0/3** | 1,634 s | checks could not run in two; the best missed 4 of 34 |

Totals: ladder **26/36**, suites **2/9**.

What it shows about vanilla Pi with BF16 Mellum, at n = 3 (a screen, not a
rate):

- Small, bounded fixes are solid (rungs 1–4, and rungs 11–12 at 3/3).
- The multi-phase web-app build is where vanilla Pi fails, and mostly by its
  own hand: it starts the app in the foreground and waits, or names the app
  differently from the spec. Those are the pathologies the worker's guards and
  project facts were built for.
- Gold passes for no setup measured so far; the closest session here missed 4
  of 34 checks.
- Against the earlier oMLX 6-bit plain run (rungs 1–5: 8/15), rungs 1–5 here
  are 14/15. Weights, output cap (4,096 then, 16,384 now), server and Pi
  version all differ, so the gap is not attributable to any one of them; the
  planned llama.cpp BF16 and Q6_K arms are what would separate quantization.



## What would falsify this

- Two runs that both pass every pin check differ systematically (then the GPU
  and client pins are not enough; the host driver, region or client OS belongs
  in the pins).
- Pi's tool calls or reasoning fail to parse under the pinned flags.
- `enable_thinking: false` does not reach the template through vLLM.

## Risks

- Sampling is at temperature 1.0 and vLLM batching is not bit-deterministic,
  so a replicate reproduces a distribution, not a transcript; n has to carry
  that.
- The A6000 offers are few (three on the day), so a replicator may wait for
  one. The pin is the card, not the provider: any host with it and the image
  will do.
- Tunnel latency and the client machine change wall time, not scores; the
  manifest shows where a run ran.
- A model-started server on the client outlives its session when it is not in
  the harness's process group (the BACKLOG "leak sweep" entry): screen 1 left
  one on port 8000, killed by hand.
- Pins age: the image or revision may be pulled upstream. The digest and
  revision still identify exactly what was run.
