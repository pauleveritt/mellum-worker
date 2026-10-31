---
title: Base Pi on llama.cpp
track: getting-started
position: 1
prerequisites: []
authors: [Paul Everitt, Andre van Zuydam]
backends: [llamacpp]
---

# Base Pi on llama.cpp
Pi is a minimal agent harness with a feedback loop, tools and prompts already built in. It works out of the box for
most large language models. By the end of this step, a machine that had no Python runs a local Mellum and answers a
prompt through base Pi: Pi with no worker, no extensions and none of your own settings or our enhancements.
It takes a few commands and one large download.

Everything runs from a clone of `mellum-worker`, because the settings and the
Pi profile are files in this repo; in later steps we'll add our own harness and extensions.

![A small robot setting up a laptop next to a llama figurine and a small server box](../assets/illustrations/base-pi-on-llamacpp.webp){ .illustration }

## What you need

- A terminal. The commands below are for macOS on Apple Silicon, where this
  repo has smoke-tested the backend. On Linux and Windows, install
  `llama-server` from the [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases) and put it on `PATH`; the `uv`,
  `uvx` and Pi commands are the same, with the PowerShell profile line in
  step 6.
- About 10 GB free: the `Q4_K_M` weights are 8.1 GB, and the server peaked at
  8.38 GB with a 50,000-token context.

## 1. Install uv, npm, Pi & llama.cpp server 

We need a server that can serve LLMs in an efficient way that works with a smaller memory format, cross-platform.
Additionally, we need package managers for Python and Node.js, which run the tools we are going to use. Pi is also installed.
For your convenience there is an installation script at the root of your clone, for Windows and for Linux / macOS:

**Linux / macOS**
```bash
bash ./install.sh
```

**Windows**
```cmd
.\install.bat
```

After running the script, check that you have a working system:

```
llama-server --version
uv --version
npm --version
pi --version
```

If you get any errors, you will have to [troubleshoot](troubleshoot.md) until you get it working.

## 2. Let `pyproject.toml` choose Python

This repo's `pyproject.toml` says `requires-python = ">=3.14"`. That line is
the whole reason no Python is needed up front: `uv run` reads it, fetches
that interpreter if the machine has none, and runs the command in a project
environment.

```toml
[project]
requires-python = ">=3.14"

[tool.mellum]
model = "JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M"
context = 50000
max_tokens = 16384
temperature = 1.0
top_p = 0.95
top_k = 20
```

`[tool.mellum]` is the one place model settings live. The server, `chat` and
the Pi profile are generated from it, so changing a value here changes every
one of them together.

## 3. Fetch the tools a later step grades with

`uvx` runs a Python tool without installing it into the project:

```
uvx ruff --version
uvx pyrefly --version
uvx complexipy --version
```

That first run downloads and caches each tool, so the grading in a later
lesson will not turn into a setup detour.

## 4. Start the server

```
uv run scripts/backend.py start
uv run scripts/backend.py status
```

The first `start` downloads `Q4_K_M` through llama.cpp's `-hf`, so it takes a
while; the command waits for health and prints the pid and log path. `status`
then reports `up on 127.0.0.1:8002` and its `n_ctx`: 50176 on this machine,
because the server pads the 50,000 it was asked for.

The settings become llama.cpp's flags: `-c 50000` from `context`, and the
model name from `[tool.mellum]`. Everything else (the batch sizes, the
`q8_0` KV cache, Metal offload) is the 16 GB profile written into
`scripts/backend.py`, and `scripts/backend.py` is short enough to read.

## 5. Chat once

```
uv run scripts/backend.py chat "In one sentence, what makes a test useful?"
```

The reply goes to stdout; the model's thinking and the token count go to
stderr. `temperature`, `top_p` and `top_k` are the values from
`pyproject.toml`, not hidden defaults.

## 6. Connect Pi

The repo carries a private Pi profile at `learn/code/profile/`, generated
from `[tool.mellum]`. Point Pi at it and ask for one line:

Linux / macOS
```bash
export PI_CODING_AGENT_DIR=$PWD/learn/code/profile
```
Windows (cmd)
```cmd
set "PI_CODING_AGENT_DIR=%CD%\learn\code\profile"
```

Windows (PowerShell)
```powershell
$env:PI_CODING_AGENT_DIR = "$PWD\learn\code\profile"
```

After setting the environment variable, run your first Pi command:

```
pi -p --provider llamacpp --model Mellum2.1-12B-A2.5B-Thinking --no-approve --no-extensions --no-skills --no-prompt-templates --no-themes --no-context-files --no-session "Say hello in one line."
```

You should see "Hello" in response.

What those flags buy you: your own `~/.pi` is neither read nor written, the
repo's `AGENTS.md` does not load, and no extension or skill is discovered.
The run is base Pi on the model: the baseline the next lessons build on.
`--no-approve` is there because the profile is the only configuration this
run should trust.

## 7. Stop it

```bash
uv run scripts/backend.py stop
```

## What you have

A local Mellum on llama.cpp, a one-command chat, and base Pi answering
through a profile that lives in the repo. Next, [Working With Pi](working-with-pi.md)
opens Pi's interactive terminal: prompts, tools, sessions, and the two
commands this course adds.
