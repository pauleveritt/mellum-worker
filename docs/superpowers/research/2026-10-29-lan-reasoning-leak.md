# The LAN vLLM host returns reasoning as text after the first turn

**What is measured.** On the LAN host (`http://192.168.88.99:11485/v1`, vLLM
`0.26.1rc1.dev1102+ge9d1398d9`, model id `mellum`, the 6-bit Mellum), a
**streamed** turn that follows a tool result comes back with the reasoning in
`content`, opened by a literal `<think>`, and no reasoning field. Pi always
streams.

- Replayed by hand, one user turn, one assistant tool call, one tool result:
  streamed 4 of 4 leaked; the same request without streaming separated the
  reasoning 4 of 4, with and without `preserve_thinking`.
- In the harness traces of 2026-10-29 on this host (eight sessions, the
  running-commands screen and the E4 check): **236 of 244** assistant turns
  carry `<think>` text; the 8 clean ones are each session's first turn.
- On the pinned baseline (vast.ai A6000, vLLM 0.32.0,
  `--reasoning-parser qwen3 --tool-call-parser hermes`, `scripts/baseline/`),
  six running-commands sessions: **0 of 136** turns carry `<think>` text; every
  turn has a reasoning field.

**What is conjecture.** That the cause is the LAN host's vLLM build (a
development build older than the pin) and its streaming reasoning parser,
not Pi or the profile: Pi sends earlier reasoning back in a `reasoning` field
with `chat_template_kwargs: {enable_thinking: true, preserve_thinking: true}`,
the same on both hosts, and only the LAN host's streamed replies differ.

## What it changes

- **Display.** In Pi, every turn after the first shows the model's reasoning
  as reply text.
- **Context.** Pi sends that text back as assistant content on every later
  request, not as reasoning, so the model sees its earlier reasoning as
  things it said. That differs from the pinned baseline.
- **Evidence.** Every lesson-check session on this host so far ran under it:
  the running-commands 6-bit screen and the E4 revision 3 attempts. Those
  results carry a serving confound and are read as such.

## The fix

On the host: serve with the pinned stack, vLLM 0.32.0 with
`--reasoning-parser qwen3 --tool-call-parser hermes`, as
`scripts/baseline/serve.sh` does. Then replay the streamed follow-up turn; it
must come back with a reasoning field and no `<think>` in `content`.

## What would falsify this

The pinned vLLM 0.32.0 serving the same 6-bit weights and still leaking on a
streamed follow-up: then the cause is the weights or their template, not the
vLLM build.

## Risks

The LAN host's launch flags are not visible from outside; the parser it runs
is inferred from its behaviour.
