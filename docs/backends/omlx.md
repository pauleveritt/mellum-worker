# Backend: oMLX on Apple Silicon (superseded)

> **Superseded.** The shipped recipe now serves Mellum on the local
> llama.cpp backend — see [`llamacpp.md`](llamacpp.md) and
> `uv run scripts/backend.py start`. oMLX support has been retired; this page
> is kept for historical reference (the shipped pass-rates were measured on
> it) and for the MLX weights the Apple-Silicon
> [`mlx-lm.md`](mlx-lm.md) path still uses. The `omlx` provider template and
> the server-settings check it describes no longer ship.

Everything below is what the retired setup did, for the record.

## Weights

```bash
hf download pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit \
  --local-dir ~/.cache/huggingface/hub/Mellum2.1-12B-A2.5B-Thinking-6bit
```

9.9 GB, two safetensors shards, MLX affine 6-bit, group size 64, MoE
routers at 8 bits. The folder name is the model id every config uses.

## Serve

```bash
omlx serve \
  --model-dir "$HOME/.cache/huggingface/hub" \
  --host 127.0.0.1 --port 8001 \
  --max-concurrent-requests 1 --hot-cache-max-size 0 --memory-guard-gb 14
```

`--model-dir` is the parent of the model folder. The menu-bar app works
the same way: add that parent directory and set the same options.

## Per-model settings

In the admin page at `http://127.0.0.1:8001/admin`, or via
`PUT /admin/api/models/Mellum2.1-12B-A2.5B-Thinking-6bit/settings`:

| setting | value |
| --- | --- |
| `max_context_window` | 56000 |
| `max_tokens` | 16384 |
| `forced_ct_kwargs` | `["enable_thinking"]` |
| `enable_thinking` | true |
| `thinking_budget_enabled` | false |
| `max_tool_result_tokens` | `null` (unset) |
| TurboQuant / cache quantization | off |

Clients send their own `max_tokens`, sampling, penalties and
`chat_template_kwargs`, and oMLX gives the request precedence over the
profile: Pi sends `max_tokens` 16,384, sampling and thinking on with every
request. Two exceptions run the
other way: `forced_ct_kwargs` makes the server's `enable_thinking` win over
the request, and `force_sampling` on makes the server's temperature, top_p
and top_k win, so keep those at thinking on and 1 / 0.95 / 20. The context
window, TurboQuant, thinking budget and tool-result cap are server-only; no
request changes them. `/mellum check` fails on any of these.

## Memory

Measured on an M5 Max with 128 GB: a cold 50,000-token prompt plus 4,096
generated tokens peaked at 11.74 GiB physical memory. A 16 GB machine was
not tested; the memory guard of 14 is a starting ceiling, not a promise.
