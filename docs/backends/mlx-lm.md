# Backend: a plain mlx_lm.server (a non-oMLX `--provider` ladder path)

An alternative to oMLX for running and measuring Mellum on Apple Silicon: a
plain, fully scriptable `mlx_lm.server`, driven by the ladder with a non-oMLX
`--provider` (no oMLX admin API, so the server's launch flags, not the ladder,
set the server-only values).

Changed 2026-10-24: this path was first built as `--backend mlx-lm` plus
`--model-id`. Those flags were lost from `main` in the 2026-10-22 upstream
merge, and Paul's LC.3B `--provider`, `--base-url` and `--model provider/id`
do the same job, so the restore uses them. The commands below are updated; the
history in the sections that follow is kept as it was found. This file records how to run it and
the issues hit the first time, so the next person does not rediscover them.

Verified once, as a smoke (not the measured suite): rung 1, direct mode,
`--profile tuned`, scored **pass** through Pi 1.3.0 → `mlx_lm.server` → Mellum,
7 requests, ~22 s. n = 1; a measured claim still needs a preregistered run.

## What you need (oMLX is NOT one of them)

- **The weights** (`docs/backends/omlx.md` §Weights) in a local folder.
- **`mlx_lm`** (`pip install mlx-lm` into a venv) to serve them.
- **The Pi CLI** — the ladder launches every run through `pi`. Install with
  `npm install -g @earendil-works/pi-coding-agent` (Node >= 22.19) or
  `curl -fsSL https://pi.dev/install.sh | sh`; verify `pi --version`.
- You do **not** need the oMLX app. That is the whole point of this path: the
  request-level values (sampling, max_tokens) are sent by the ladder through a
  generated Pi `models.json`, so a plain OpenAI-completions server is enough.

## Serve

```bash
HF_HUB_OFFLINE=1 python -m mlx_lm.server \
  --model /abs/path/to/Mellum2.1-12B-A2.5B-Thinking-6bit \
  --host 127.0.0.1 --port 11500 \
  --prompt-cache-size 4 --prompt-cache-bytes 4294967296 \
  --chat-template-args '{"enable_thinking": true}' \
  --max-tokens 16384
# the served id is whatever mlx_lm canonicalises --model to (usually that
# absolute path); read it from GET /v1/models.
```

Why those extra flags (the bare `--model`/`--host`/`--port` form runs, but
crawls on multi-turn agent loops):

- **`--prompt-cache-size 4 --prompt-cache-bytes 4294967296`** — keep the prompt
  cache across the agent loop's turns. Each turn re-sends the whole (growing)
  transcript; without the cache, every turn re-processes it from scratch and a
  mediated run drags. The 4 GiB ceiling holds a few concurrent sequences.
- **`--chat-template-args '{"enable_thinking": true}'`** — Mellum is a thinking
  model; this turns thinking on by default. It is a *default*: a request can
  still override per call with `chat_template_kwargs.enable_thinking` (this is
  how the ladder's `--effort-ramp` runs early slices thinking-off).
- **`--max-tokens 16384`** — the per-turn generation cap, matching the ladder's
  `tuned` profile so the server does not truncate a long thinking turn.

Then run the ladder against it, passing that served id after `mlx-lm/` in `--model`:

```bash
cd ladder
SERVED=$(curl -s http://127.0.0.1:11500/v1/models | python -c \
  "import sys,json;print(json.load(sys.stdin)['data'][0]['id'])")
uv run --offline python -m ladder.run_ladder \
  --mode direct --provider mlx-lm --base-url http://127.0.0.1:11500/v1 \
  --model "mlx-lm/$SERVED" --profile tuned --rung 1 --repeat 1 --out ../evals/<name>
```

## Issues hit, and the fix

1. **Model-id mismatch -> a HuggingFace 404 (the big one).**
   `mlx_lm.server` canonicalises its served model id to the **absolute path**
   of the weights (see `GET /v1/models`). The ladder's direct mode sends the
   short id `Mellum2.1-12B-A2.5B-Thinking-6bit`. When the request's `model`
   does not match a loaded model, `mlx_lm.server` treats it as a **HF repo_id
   and tries to fetch it**, failing with
   `Repository Not Found for url: https://huggingface.co/api/models/Mellum2.1-...`
   (a 404/401), and the run scores `error` with 0 requests.
   **Fix:** pass **`--model-id <served id>`** (the id from `GET /v1/models`, usually
   the weights' absolute path) so the request carries the id the server actually
   serves. The serve recipe above does exactly this. (Before `--model-id` existed
   the only workaround was launching the server from inside the weights' parent
   dir with the bare dir name so the short id resolved locally; `--model-id`
   replaces that trick.)

2. **Set `HF_HUB_OFFLINE=1` on the server.** It stops a model-id miss from
   turning into a slow (or hanging, on an air-gapped box) HuggingFace network
   call, and forces local resolution. Keep `HF_HOME` project-local too.

3. **Lazy load.** `mlx_lm.server` answers `/v1/models` before the weights are
   in memory; the first chat request pays the load. Warm it with a 1-token
   request if you are timing throughput.

4. **One model at a time.** The 6-bit weights are ~9.9 GB and serving peaks
   ~10-12 GB. On a 48 GB machine, other resident MLX servers were evicted when
   Mellum loaded. Serve only the model you are measuring.

5. **Thinking model + `/v1/completions` quirk.** Against the raw completions
   endpoint, `mlx_lm.server` parses a `<tool_call>` out of the `text` field and
   returns `finish_reason: tool_calls` with empty text. Use
   `/v1/chat/completions` (the ladder and Pi do) to get parsed `tool_calls`.

## Resolved: the `--model-id` override

*Now `--model provider/id` (2026-10-24).* The id after the first `/` is what the
request carries, so `--model mlx-lm//abs/path/Mellum-x` sends `/abs/path/Mellum-x`.

The ladder used to hardcode the model id it sends (`MODEL_ID`), so a real
`mlx_lm.server` — which serves under whatever id it canonicalised, usually a
path — only worked via the cwd + bare-name trick. `--model-id` (direct mode)
now sets the id the request carries, so it can match any served id directly.
Default is the Mellum id, so the oMLX path is unchanged. Verified as a smoke:
rung 1 scored `pass` with `--model-id` set to the served absolute path, no cwd
trick (n = 1, not the measured suite).

## Settings parity (honest limits)

A plain `mlx_lm.server` has no admin API, so the oMLX server-only values
(`max_context_window`, `thinking_budget`, `max_tool_result_tokens`,
`forced_ct_kwargs`) are set, if at all, by `mlx_lm.server` launch flags and do
not all have equivalents. An oMLX-vs-mlx-lm result is therefore a harness
finding about servers, not a claim about the shipped worker; see the BACKLOG
entry "Benchmark a plain mlx_lm.server against oMLX".
