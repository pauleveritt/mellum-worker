# Phase 3: Server

Check: `curl -s http://127.0.0.1:8001/v1/models` returns JSON whose `data`
array contains an entry with `"id": "Mellum2.1-12B-A2.5B-Thinking"`.

If the port does not answer, start the local server:

```bash
uv run scripts/backend.py start
```

It launches `llama-server` on `127.0.0.1:8001`, downloading the Q4_K_M
weights on the first run (~7.7 GB, progress reported), and waits for the
server to answer. It stays running in the background; stop it with
`uv run scripts/backend.py stop` and check it with
`uv run scripts/backend.py status`. Wait for the check above to pass.

Settings are fixed at launch — there is nothing to set per model. `backend.py`
reads them from `[tool.mellum]` in the repo's `pyproject.toml`:

| key | value | why |
| --- | --- | --- |
| context | 50000 | the measured context window; `llama-server -c` sets it at launch |
| max_tokens | 16384 | the per-turn budget Pi sends with every request |
| temperature / top_p / top_k | 1 / 0.95 / 20 | the model card's agentic sampling, sent per request |

`llama-server` has no admin API and no mutable per-model profile, so there is
nothing to PUT and nothing that can drift except the launched context window;
`/mellum check` (phase 6) confirms the server is up, the model is served, and
the context window is at least 50,000.
