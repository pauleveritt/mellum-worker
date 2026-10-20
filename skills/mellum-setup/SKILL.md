---
name: mellum-setup
description: Set up Mellum 2.1 as a bounded coding worker in OpenCode or Pi. Use when the user asks to install, configure, or verify Mellum Worker or Mellum Mode, or to get the Mellum model running on oMLX. Walks through weights, server, provider, agent, rules, a smoke test, and optional project facts for Mellum Mode, one checked phase at a time.
---

# Mellum setup

You are installing the Mellum Worker recipe into the user's own configuration.
Work one phase at a time. Each phase has a check; run the check first, and
skip the phase when it already passes. Before writing to any file that
exists, show the user what will change and wait for a yes.

Set `PKG` to the package root: the directory two levels above this SKILL.md.
Pi shows the skill's path when it lists skills; OpenCode's skill tool prints
the skill's base directory. Pi clones to
`~/.pi/agent/git/github.com/pauleveritt/mellum-worker`; OpenCode installs under
`~/.cache/opencode/packages/*/node_modules/mellum-worker`.

```bash
PKG=~/.pi/agent/git/github.com/pauleveritt/mellum-worker
```

Every command below is relative to `$PKG`.

## Which host am I in?

- Pi: the `/skill:` command form exists and `~/.pi/agent/settings.json` is present.
- OpenCode: the `skill` tool loaded this file and `~/.config/opencode/` is present.

Record the answer; phases 4 and 5 differ by host.

## Phases

| # | Phase | Check that means "already done" | Reference |
| --- | --- | --- | --- |
| 1 | Preflight | Apple Silicon, oMLX installed, host known | [reference/01-preflight.md](reference/01-preflight.md) |
| 2 | Weights | model folder with two `.safetensors` shards exists | [reference/02-weights.md](reference/02-weights.md) |
| 3 | Server | `GET http://127.0.0.1:8001/v1/models` lists the model | [reference/03-server.md](reference/03-server.md) |
| 4 | Provider | the host's model list shows `omlx/Mellum2.1-12B-A2.5B-Thinking-6bit` | Pi: [reference/04-provider-pi.md](reference/04-provider-pi.md), OpenCode: [reference/04-provider-opencode.md](reference/04-provider-opencode.md) |
| 5 | Worker | `mellum-worker` agent file exists in the host's user agents dir | Pi: [reference/05-worker-pi.md](reference/05-worker-pi.md), OpenCode: [reference/05-worker-opencode.md](reference/05-worker-opencode.md) |
| 6 | Rules | user accepted or declined the AGENTS.md fragment | [reference/06-rules.md](reference/06-rules.md) |
| 7 | Smoke test | the calculator fixture's tests exit 0 after the worker ran | [reference/07-smoke.md](reference/07-smoke.md) |
| 8 | Project facts (optional, Pi) | the project's `AGENTS.md` has a heading that is exactly `## Mellum` (not `## Mellum Worker`), or the user declined | [reference/08-project-facts.md](reference/08-project-facts.md) |

Read a phase's reference file only when its check fails. Phase 8 is
optional and per project; offer it in Pi once phase 7 passes. When the
checks pass, tell the user:

- Pi: "Mellum Worker is available to pi-subagents as `mellum-worker`, and
  `/mellum <task>`, `/mellum on`, `/mellum off` run Mellum Mode in this session."
- OpenCode: "Mellum Worker is the `mellum-worker` subagent. Ask your main
  agent to delegate a bounded task to it."

Using the worker well: do not rely on its own "done". Give it a *named
failing test* and re-run that test yourself afterwards — the worker's best
measured shape is a named failing test (rung 4: three files, 3/3 in every
arm), and a run can otherwise exit on an incomplete test it wrote itself.
Writing the test from the full spec first — the mediated test — is the
recommended practice and the subject of M.11; it is unmeasured today. This is
guidance, not a measured setting.

Do not invent settings. Every number in this skill was measured; if a
reference file does not cover the user's situation, say so and stop.
