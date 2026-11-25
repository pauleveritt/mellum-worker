#!/usr/bin/env python3
"""Check a tuned Mellum GGUF and publish it to Hugging Face with a full model card.

Dry run (the default) runs every check and writes the card, checksums and results to `--stage`, so the page
can be read before anything leaves the machine. `--upload` creates the repo PRIVATE and uploads; making it
public is left to the owner, by hand, after reading it there.

Checks, all required before `--upload`:
- the tuned GGUF's architecture keys and chat template match the base GGUF exactly (a converted model that
  lost its template would break tool calling for everyone who downloads it);
- a llama-server running the tuned GGUF with `--jinja` returns a parsed tool call (`--smoke-url`).
"""
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_MODEL = "JetBrains/Mellum2.1-12B-A2.5B-Thinking"
GITHUB = "https://github.com/andrevanzuydam/mellum-worker"
# Keys that may differ between two correct GGUFs of the same architecture
FREE_KEYS = ("general.", "split.", "quantize.", "GGUF.")


def compare_meta(base, ours):
    """Problems that make `ours` unsafe to publish as a drop-in for `base`."""
    problems = []
    if base.get("tokenizer.chat_template") != ours.get("tokenizer.chat_template"):
        problems.append("tokenizer.chat_template differs from the base model's")
    for key, value in sorted(base.items()):
        if key.startswith(FREE_KEYS) or key == "tokenizer.chat_template":
            continue
        if key not in ours:
            problems.append(f"{key} is missing")
        elif ours[key] != value:
            problems.append(f"{key} is {ours[key]!r}, base has {value!r}")
    return problems


def gguf_meta(path):
    """Every metadata field of a GGUF except the vocabulary arrays."""
    from gguf import GGUFReader

    out = {}
    for key, field in GGUFReader(str(path)).fields.items():
        if key.startswith("tokenizer.ggml.") and key not in ("tokenizer.ggml.model", "tokenizer.ggml.pre"):
            continue
        try:
            out[key] = field.contents()
        except Exception:  # a field gguf can't decode is compared as absent on both sides
            continue
    return out


def sha256_lines(paths):
    lines = []
    for path in paths:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 24), b""):
                digest.update(block)
        lines.append(f"{digest.hexdigest()}  {Path(path).name}")
    return lines


def smoke_tool_call(url, model):
    """Problems with a live server's tool calling: it must return a parsed call, not text."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "Read the file app.py."}],
        "tools": [{"type": "function", "function": {
            "name": "read", "description": "Read a file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}],
        "max_tokens": 2048,
    }
    request = urllib.request.Request(f"{url}/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        message = json.load(response)["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    if not calls:
        return [f"no parsed tool call; content was {str(message.get('content'))[:200]!r}"]
    if calls[0]["function"]["name"] != "read" or "app.py" not in calls[0]["function"]["arguments"]:
        return [f"unexpected tool call {calls[0]['function']}"]
    return []


def _size(n):
    return f"{n / 1e9:.1f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB"


def render_card(info):
    """The model card: what it is, how to run it, how it was made, what it scored and where it falls short."""
    repo, gguf, commit = info["repo"], info["gguf"], info["commit"]
    data_url = f"{GITHUB}/tree/{commit}/{info['data']}"
    rows = "\n".join(f"| {r['model']} | {r['passed']}/{r['n']} | {r['tool_error_rate']:.0%} |"
                     for r in info["results"])
    files = "\n".join(f"| {name} | {_size(size)} | `{digest[:16]}…` |" for name, size, digest in info.get("files", []))
    return f"""---
base_model: {BASE_MODEL}
license: apache-2.0
language:
- en
pipeline_tag: text-generation
library_name: gguf
tags:
- gguf
- mellum
- dpo
- coding-agent
- tool-calling
---

# {repo.split("/")[-1]}

A preference-tuned build of [{BASE_MODEL}](https://huggingface.co/{BASE_MODEL}) for one job: working as a bounded
coding agent inside the [Pi](https://github.com/earendil-works/pi) harness, calling `read`, `bash`, `edit` and `write`
to change a small Python project until its tests pass, then stopping. It is an experiment from
[mellum-worker]({GITHUB}), not a general upgrade of the base model.

## What this is

- **Base:** {BASE_MODEL}, a 12B mixture-of-experts model with 2.5B active parameters and a thinking channel.
- **Change:** a LoRA adapter trained with DPO (IPO loss) on the base model's own Pi runs, merged and quantised to
  `{gguf}`.
- **Aim:** keep the base model's tool calling intact while preferring the ways of working that passed hidden tests,
  and the tool call that recovered from a failed one.
- **Not aimed at:** chat, general knowledge, or code completion outside an agent loop. Nothing here was measured
  for those.

## How to run it

Serve it with llama.cpp. `--jinja` is required: tool calls are parsed by the chat template built into the GGUF.

```bash
hf download {repo} {gguf} --local-dir .
llama-server -m {gguf} --jinja -c 50000 -fa auto -ngl 999 \\
  -ctk q8_0 -ctv q8_0 --host 127.0.0.1 --port 8001 -a mellum
```

Then point any OpenAI-compatible client at `http://127.0.0.1:8001/v1` with model `mellum`. In Pi, add a provider
to `~/.pi/agent/models.json`:

```json
{{"providers": {{"llamacpp": {{"baseUrl": "http://127.0.0.1:8001/v1", "api": "openai-completions",
  "apiKey": "none", "models": [{{"id": "mellum", "contextWindow": 50000}}]}}}}}}
```

## How it was trained

- **Method:** DPO with the IPO loss (beta 10, so a target gap of 0.05 per token), scored against a frozen copy
  of the base model.
- **Adapter:** LoRA rank 8, scale 2.0, 81.3M trainable parameters, merged into the dequantised base before
  conversion.
- **Schedule:** {info["pairs"]} pairs, 1 epoch, 4 pairs per update ({info["updates"]} updates), learning rate 2e-5,
  sequences up to 41,000 tokens processed in 2,048-token chunks.
- **Hardware:** Apple M3 Max with MLX (`mlx-lm` 0.32.2); conversion with llama.cpp `convert_hf_to_gguf.py` and
  `llama-quantize`.
- **Gate:** the adapter is only converted if its margin on held-out pairs ends above zero. This one ended at
  {info["heldout_margin"]:+.4f}.

## Training data

All pairs come from the base model's own recorded runs on the mellum-worker task suites, graded by hidden tests.
The exact set, with how it was built, is at [{info["data"]}]({data_url}).

- **Phase pairs:** a run that passed a phase's hidden tests against one that failed the same phase. Only that
  phase's turns are scored; earlier phases are context.
- **Step pairs:** at the same point in a run, the tool call that recovered from a failed `read`, `edit`, `write` or
  `ls` against the failed call. Only the tool call is kept, so the error message never leaks into the preferred side.
- **Held out:** the Easy task the model is screened on never enters training, and validation pairs are held out by
  whole run.

## Evaluation

The Easy suite: one small FastAPI app built from a written spec, graded by hidden tests, 3 runs per model, same
server build and settings.

| Model | Easy passed | Tool-call errors |
|---|---|---|
{rows}

Three runs per model is a screen, not a rate: it can show a large gap, not a small one.

## Limitations

- One harness (Pi), one model family, and small task suites written in one style. Behaviour elsewhere is unmeasured.
- The preference data is the base model's own work, so the tune can only prefer habits the base already has.
- Q4_K_M quantisation; other quantisations were not evaluated.
- Thinking is on, as in the base model; runs are slower than a non-thinking model.

## Files

| File | Size | SHA-256 |
|---|---|---|
{files}

Full checksums are in `SHA256SUMS`. The `adapter/` folder holds the LoRA adapter, to rebuild from the base model.

## Reproduce

Everything is at commit [`{commit}`]({GITHUB}/tree/{commit}): the pair builder (`learn/finetune/build_dpo_phases.py`),
the trainer (`learn/finetune/dpo_native_train.py`), the training data and its `SOURCE.md`, and this card's
generator (`learn/finetune/publish_hf.py`).

## Licence

Apache 2.0, the same as the base model. The base model is by JetBrains; this adapter and the build are by
[andrevanzuydam](https://huggingface.co/andrevanzuydam).
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gguf", type=Path, required=True)
    ap.add_argument("--base-gguf", type=Path, required=True)
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--results", type=Path, required=True, help="JSON list of {model, passed, n, tool_error_rate}")
    ap.add_argument("--data", required=True, help="repo path of the training set")
    ap.add_argument("--pairs", type=int, required=True)
    ap.add_argument("--updates", type=int, required=True)
    ap.add_argument("--heldout-margin", type=float, required=True)
    ap.add_argument("--stage", type=Path, required=True)
    ap.add_argument("--smoke-url", help="a llama-server serving --gguf with --jinja, e.g. http://127.0.0.1:8001/v1")
    ap.add_argument("--upload", action="store_true")
    a = ap.parse_args()

    problems = compare_meta(gguf_meta(a.base_gguf), gguf_meta(a.gguf))
    if a.smoke_url:
        problems += smoke_tool_call(a.smoke_url, "mellum")
    elif a.upload:
        problems.append("--upload needs --smoke-url: tool calling must be checked on a live server first")
    if a.heldout_margin <= 0:
        problems.append(f"held-out margin {a.heldout_margin} is not positive")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    if subprocess.run(["git", "status", "--porcelain", "--", a.data], capture_output=True, text=True).stdout.strip():
        problems.append(f"{a.data} has uncommitted changes: the card would link data that isn't in the commit")

    sums = sha256_lines([a.gguf])
    a.stage.mkdir(parents=True, exist_ok=True)
    info = {"repo": a.repo, "gguf": a.gguf.name, "commit": commit, "data": a.data, "pairs": a.pairs,
            "updates": a.updates, "heldout_margin": a.heldout_margin, "results": json.loads(a.results.read_text()),
            "files": [(a.gguf.name, a.gguf.stat().st_size, sums[0].split()[0])]}
    (a.stage / "README.md").write_text(render_card(info))
    (a.stage / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    (a.stage / "results.json").write_text(json.dumps(info["results"], indent=2) + "\n")
    print(f"card: {a.stage / 'README.md'}")
    print(f"page: https://huggingface.co/{a.repo}")
    if problems:
        print("CHECKS FAILED:\n- " + "\n- ".join(problems))
        sys.exit(1)
    print("checks passed")
    if not a.upload:
        print("dry run: nothing uploaded")
        return

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(a.repo, private=True, exist_ok=True)
    for name in ("README.md", "SHA256SUMS", "results.json"):
        api.upload_file(path_or_fileobj=str(a.stage / name), path_in_repo=name, repo_id=a.repo)
    api.upload_folder(folder_path=str(a.adapter), path_in_repo="adapter", repo_id=a.repo,
                      allow_patterns=["adapters.safetensors", "adapter_config.json"])
    api.upload_file(path_or_fileobj=str(a.gguf), path_in_repo=a.gguf.name, repo_id=a.repo)
    print(f"uploaded PRIVATE: https://huggingface.co/{a.repo}")


if __name__ == "__main__":
    main()
