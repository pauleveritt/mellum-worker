# Backend: llama.cpp on Apple Silicon

**Smoke-tested, not ladder-measured.** A single request round-tripped
through `/v1/chat/completions` with tools, thinking on, at 50k context.
No rung has been rerun, so no number here belongs in the README's status
table. Measured on an M5 Max, 128 GB; a 16 GB machine was not run.

## Install

```bash
brew install llama.cpp     # 0.7.0, build 11669 when this was written
llama-server --version
```

Metal is the default on Apple Silicon. `--jinja` is on by default in this
build, and the GGUF's own chat template is used — the model ships a ChatML
`<|im_start|>` template, which llama.cpp picks up without help.

## Weights

`JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF` publishes BF16 and four
quants. `scripts/backend.py` passes the model to `llama-server -hf`, which
downloads and caches it in the Hugging Face cache on first start.

| File | Size |
| --- | --- |
| `MXFP4_MOE` | 7.0 GB |
| `Q4_K_M` | 8.1 GB |
| `Q6_K` | 10.9 GB |
| `Q8_0` | 12.9 GB |
| `BF16` | 24.3 GB |

## Serve

`scripts/backend.py` wraps this; `[tool.mellum]` in the root
`pyproject.toml` is the whole config. No daemon, no launch agent — the
model is resident only while a server runs. The script serves the 16 GB
profile: `Q4_K_M`, 50k context, `-b/-ub 512`, `q8_0` KV.

```bash
uv run scripts/backend.py serve     # foreground
uv run scripts/backend.py start     # background + pidfile + health wait
uv run scripts/backend.py status    # up/down, and the server's n_ctx
uv run scripts/backend.py stop
uv run scripts/backend.py kill      # every llama-server, whatever started it
uv run scripts/backend.py chat "prompt"   # one-shot; thinking to stderr
```

The command `start` runs:

```bash
llama-server -hf JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M \
  -a Mellum2.1-12B-A2.5B-Thinking --host 127.0.0.1 --port 8002 \
  -c 50000 -np 1 --jinja -fa auto -b 512 -ub 512 \
  -ctk q8_0 -ctv q8_0
```

There is no `-ngl`: llama.cpp's `--fit` puts as many layers on the GPU as
free memory allows and keeps the rest on the CPU. On Apple Silicon that is
every layer; on an 8 GB laptop GPU it is a split. `-c` is set, so `--fit`
never lowers the context.

2026-10-20: the Justfile that shipped in `b51a1e8` was retired before
release for `scripts/backend.py`. The Learning Center's learner installs
`uv` anyway, the same file can hold the settings, and the flags stay
readable in Python instead of shell recipes.

## Settings, against the oMLX recipe

| oMLX (measured) | llama.cpp | Note |
| --- | --- | --- |
| `max_context_window` 56000 | `-c 56000` | the script serves 50k (`[tool.mellum] context`) |
| `max_tokens` 16384 | client `max_tokens` | from `[tool.mellum] max_tokens` |
| `force_sampling` 1 / 0.95 / 20 | `temperature`/`top_p`/`top_k` per request | from `[tool.mellum]`, sent by `chat` and Pi |
| `forced_ct_kwargs` thinking on | `--reasoning on` | server-side, closest equivalent; not yet exercised on the ladder |
| `--max-concurrent-requests 1` | `-np 1` | |
| TurboQuant off | `-ctk/-ctv f16` | the hybrid cache stays native; `q8_0` only for the 16 GB preset |
| memory guard | none | `-b`/`-ub` and the quant are the only levers |

## Measured so far

| Run | Peak RSS | Generation | Prompt eval |
| --- | --- | --- | --- |
| Q4_K_M, 50k ctx, `-b/-ub 512` | 8.38 GB | 207.6 tok/s | 72.2 tok/s |
| BF16, 8k ctx, default batch | not recorded | 101.5 tok/s | 66.0 tok/s |

Tool calls parse: a `read` request came back as
`finish_reason: "tool_calls"` with `{"path": "/etc/hosts"}`.

## Why 50k context is cheap here

28 layers, but only 7 are full-attention; the other 21 are sliding-window
at 1024. KV at 50 000 tokens is `7 x 50000 x 1024 B + 21 x 1024 x 1024 B`
= 0.38 GB at f16, 0.20 GB at `q8_0`. Weights, not context, set the memory
budget: Q4_K_M peaks at 8.38 GB, which is what makes a 16 GB machine
plausible for the first time.

## Open

- Rungs 1–5 have a reference run ([record](../ladder/reference-llamacpp-rungs1-5/README.md)):
  14/15, one rung-4 failure on the `max_tokens` cap. Rungs 6–9 have not been
  run on llama.cpp, so nothing is comparable to the oMLX numbers yet.
- A 16 GB machine is untested; 8.38 GB leaves room for macOS but the
  wired limit and the GPU allocator were not observed there.
- Thinking is forced with `--reasoning on`, not with the oMLX
  `forced_ct_kwargs` mechanism; whether clients can override it has not
  been checked.
- The script exposes the 16 GB profile only. The BF16 56k server from the
  old Justfile is a hand command now, not a recipe.
- A rung-1 smoke ran through the ladder on 2026-10-20 (`--mode direct
  --profile baseline --provider llamacpp --base-url http://127.0.0.1:8002/v1
  --model llamacpp/Mellum2.1-12B-A2.5B-Thinking --context-window 50000`):
  PASS, 7 requests, no tool errors. It is a smoke, not a reference run;
  nothing from it is in `evals/`.
