# Phase 4 (Pi): Provider

Check: `pi --list-models Mellum2.1 2>/dev/null | grep -Eq '^llamacpp +Mellum2\.1-12B-A2\.5B-Thinking'`
Pi prints provider and model as two columns, no slash. (If that flag is absent
in the user's Pi, inspect `~/.pi/agent/models.json` for a `llamacpp` provider
with a model id `Mellum2.1-12B-A2.5B-Thinking`.)

If missing, merge the shipped provider profile into the user's models.json.
Preview first:

```bash
node "$PKG/scripts/merge-json.mjs" ~/.pi/agent/models.json "$PKG/templates/pi/models.llamacpp.json"
```

It prints only `providers.llamacpp` after the merge. Existing providers and
other models are kept, and a merge leaves any `baseUrl`/`apiKey` the user
already set on a `llamacpp` provider untouched; a backup is written next to
the file. With the user's yes:

```bash
node "$PKG/scripts/merge-json.mjs" ~/.pi/agent/models.json "$PKG/templates/pi/models.llamacpp.json" --write
```

If `~/.pi/agent/settings.json` has an `enabledModels` list, the model is
hidden until it is listed. Offer to add `"llamacpp/Mellum2.1-12B-A2.5B-Thinking"`
to that list; edit the file with the edit tool, do not rewrite it.

Why these fields: `supportsDeveloperRole: false` keeps Pi from sending the
system prompt as a `developer` message, which this server does not expect;
`thinkingFormat: qwen-chat-template` matches how the model emits thinking;
`maxTokens 16384` is the output limit Pi sends with each request, and
`contextWindow 50000` matches the launched server. Sampling is the model
card's agentic setting, 1 / 0.95 / 20.

Re-run the check. Restart Pi if it was open; it reads models.json at start.
