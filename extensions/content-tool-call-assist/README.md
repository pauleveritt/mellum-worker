# content-tool-call-assist

A Pi extension that lets a small open model drive the agent loop even when it
emits its tool call in the message **content** — a fenced JSON block, or a
Hermes/Qwen `<function=…>` XML block — instead of the structured `tool_calls`
field. Pi only executes structured calls, so such a turn would otherwise end
with text and no action and the loop stalls; this extension recovers the call.

It registers a provider that delegates streaming to the built-in
`openai-completions` implementation and, when a turn produced no structured
call but its content carries one, promotes it into a real tool call before the
turn settles.

- **Input shapes:** `{"tool","args"}`, `{"name","arguments"}`, and Hermes-XML
  `<function=name><parameter=k>v</parameter>`.
- **Safety:** promotion is gated on the real tool names and a present arguments
  key, so model *data* (e.g. a cart item `{"name":"Widget A"}`) is never
  mistaken for a call.
- **Optional push:** `ASSIST_FORCE_TOOLS=1` adds a late system nudge and a
  seed/temperature retry for models that need encouragement to emit a call.
- **Config:** `ASSIST_BASE_URL` / `ASSIST_MODEL_ID` point it at any
  OpenAI-compatible server.

## Install into a Pi checkout

`index.ts` here is the canonical source (also mirrored to our Pi fork). Because
its imports resolve only inside a Pi checkout, install it there:

```sh
scripts/patch-pi.sh [PI_DIR]        # PI_DIR defaults to $PI_DIR or ~/projects/pi
```

The ladder used to load it in direct mode with `--model-spec content-assist/<id>`
and `--pi-extension <PI_DIR>/packages/coding-agent/examples/extensions/content-tool-call-assist`.
`--model-spec` (Pi's `--model` set apart from the provider the ladder writes) was
not restored to the ladder on 2026-10-24; the code is at `da04888` if a
small-model screen needs it again. `--pi-extension` is available.
