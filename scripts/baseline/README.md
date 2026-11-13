# The vLLM baseline: replicate it anywhere

The baseline is **Pi and the model, nothing else**: vanilla Pi with no
plugins, extensions, skills, prompt templates or context files, driving
Mellum 2.1 on every ladder rung and every eval suite. Only vLLM runs on a
rented GPU; Pi, the ladder and the suites run on your machine and reach the
model through an SSH tunnel.

A baseline only counts if someone else can rebuild it, so everything that
defines it is pinned in [`pins.env`](pins.env): the GPU model, VRAM and minimum
driver; the vLLM image by digest; the model by Hugging Face revision; the
serving flags; the Node build (checksummed per platform), Pi and vastai
versions; and the run's rungs, repeats and deadlines. Pi's provider and
sampling are pinned in [`pi-profile/`](pi-profile/). Change a pin and you have
a new baseline, not a replicate. Why it is pinned this way: the
[research note](../../docs/superpowers/research/2026-10-28-vllm-baseline.md).

**Status:** `client` and `offers` have run (macOS, 2026-10-28). Renting,
serving, the tunnel and the run have not; the first run does that.

## Run it

You need [uv](https://docs.astral.sh/uv/), Git, an OpenSSH client (built into
macOS, Linux and Windows 10+), an SSH key, and a vast.ai account.

```bash
cp scripts/baseline/vast.env.example scripts/baseline/vast.env
# edit vast.env: replace <insert vast.ai token> with your vast.ai API key
uv run scripts/baseline/baseline.py offers   # free: what the pinned GPU costs now
uv run scripts/baseline/baseline.py all      # install, rent, serve, run, fetch, destroy
```

`all` destroys the instance on any exit, success or failure, after fetching
the vLLM log; `all --keep` leaves it up for more runs (it bills until `down`). Each step also runs on its own: `client`, `up`, `serve`,
`tunnel`, `run`, `fetch`, `down`, and `ssh` opens a shell on the box.
`vast.env` is git-ignored; the token reaches only the vastai CLI's environment.

| Step | Where | What |
| --- | --- | --- |
| `client` | here | Node and Pi at their pinned versions under `.baseline/`, Node checked against its pinned SHA-256; nothing global is touched |
| `up` | vast.ai | the cheapest verified on-demand offer of the pinned GPU under `VAST_MAX_DPH`, running the pinned image |
| `serve` | box | copies `pins.env`, `check-host.sh`, `serve.sh`; refuses another GPU, VRAM, GPU count, driver or vLLM; starts vLLM |
| `tunnel` | here | `ssh -L` from `LOCAL_PORT` to the box's vLLM |
| `run` | here | re-checks the box's GPU; refuses a dirty checkout; writes `runs/baseline-<utc>-<commit>/` |

## Windows

`client`, `offers`, `up`, `serve`, `tunnel`, `fetch`, `ssh` and `down` run
natively. `run` needs POSIX process groups (the ladder and the suites kill
whole process trees), so on Windows do the whole recipe inside WSL2: it is the
Linux recipe, with its own pinned Node and Pi.

## What runs, and what "vanilla" means

| Part | Command | n | Deadline |
| --- | --- | --- | --- |
| Ladder, rungs 1–12 | `run_ladder --mode primary --plain` | 3 | 600 s |
| Eval suites, easy/medium/hard | `harness.py run --arm bare --grade --stall 120` | 3 | 2,700 s, or 120 s on one stalled command |

Pi starts with `--no-extensions --no-skills --no-context-files` (the suites
add `--no-prompt-templates --no-themes`), its own system prompt and its own
tools. The profile installs no packages. The one thing loaded is the
**recorder**, the measuring instrument: it writes the trace the scorer reads,
and its handlers return nothing, so every request Pi sends is unchanged. Both
parts use the same profile: the vLLM provider, temperature 1.0, top-p 0.95,
top-k 20, 16,384 output tokens.

## What a run proves about itself

`manifest.json` holds the commit, every pin as run, the server's `/version`
and `/v1/models`, the box's GPUs (name, VRAM, driver) and the client (OS,
Node, Pi, uv). Each ladder `run.json` carries the server block and the Pi
version too. A run whose manifest does not match `pins.env` is not a
replicate.
