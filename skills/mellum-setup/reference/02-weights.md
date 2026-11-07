# Phase 2: Weights

The weights are the Q4_K_M GGUF of
`JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF` (about 7.7 GB). They are
fetched automatically by `llama-server -hf` the first time the server starts
(phase 3), into llama.cpp's own cache or the Hugging Face hub cache — there is
no separate download step.

Check (optional, only if the user wants to confirm before serving):

```bash
uv run scripts/backend.py verify
```

It compares the downloaded GGUF against Hugging Face's size and sha256 and
prints where it is, or says none is downloaded yet (in which case phase 3's
start will fetch it). Add `--delete` to remove a damaged copy so start
re-downloads it. If nothing is downloaded and the user has limited disk or
bandwidth, just let phase 3 do it — the first `start` reports download
progress.
