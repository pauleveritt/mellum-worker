---
name: mellum-setup
description: Set up Mellum 2.1 as a bounded coding worker in OpenCode or Pi. Use when the user asks to install, configure, or verify Mellum Worker or Mellum Worker, or to get the Mellum model running on oMLX. Walks through weights, server, provider, agent, rules, a smoke test, and optional project facts for Mellum Worker, one checked phase at a time.
---

# Mellum setup

You are installing the Mellum Worker recipe into the user's own configuration.
Work one phase at a time. Each phase has a check; run the check first, and
skip the phase when it already passes. Before writing to any file that
exists, show the user what will change and wait for a yes.

Set `PKG` to the package root: the directory two levels above this SKILL.md.
Pi shows the skill's path when it lists skills; OpenCode's skill tool prints
the skill's base directory. Pi clones to
`~/.pi/agent/git/github.com/andrevanzuydam/mellum-worker`; OpenCode installs under
`~/.cache/opencode/packages/*/node_modules/mellum-worker`.

```bash
PKG=~/.pi/agent/git/github.com/andrevanzuydam/mellum-worker
```

Every command below is relative to `$PKG`.

## Host

This skill installs the Pi side only: `~/.pi/agent/settings.json` must exist.
OpenCode is no longer supported.

## Phases

| # | Phase | Check that means "already done" | Reference |
| --- | --- | --- | --- |
| 1 | Preflight | Apple Silicon, oMLX installed | [reference/01-preflight.md](reference/01-preflight.md) |
| 2 | Weights | model folder with two `.safetensors` shards exists | [reference/02-weights.md](reference/02-weights.md) |
| 3 | Server | `GET http://127.0.0.1:8001/v1/models` lists the model | [reference/03-server.md](reference/03-server.md) |
| 4 | Provider | Pi's model list shows `omlx/Mellum2.1-12B-A2.5B-Thinking-6bit` | [reference/04-provider-pi.md](reference/04-provider-pi.md) |
| 5 | Rules | user accepted or declined the AGENTS.md fragment | [reference/05-rules.md](reference/05-rules.md) |
| 6 | Smoke test | the calculator fixture's tests exit 0 after `/mellum` ran | [reference/06-smoke.md](reference/06-smoke.md) |
| 7 | Project facts (optional) | the project's `AGENTS.md` has a heading that is exactly `## Mellum` (not `## Mellum Worker`), or the user declined | [reference/07-project-facts.md](reference/07-project-facts.md) |

Read a phase's reference file only when its check fails. Phase 7 is
optional and per project; offer it once phase 6 passes. When the checks
pass, tell the user:

- "Mellum Worker is the `/mellum <task>` command in this session, with
  `/mellum on` and `/mellum off` to manage it."

Using the worker well: do not rely on its own "done". Give it a *named
failing test* and re-run that test yourself afterwards — the worker's best
measured shape is a named failing test (rung 4: three files, 3/3 in every
arm), and a run can otherwise exit on an incomplete test it wrote itself.
Writing the test from the full spec first — the mediated test — is the
recommended practice and the subject of M.11; it is unmeasured today. This is
guidance, not a measured setting.

Do not invent settings. Every number in this skill was measured; if a
reference file does not cover the user's situation, say so and stop.
