# Lessons learned — small models as bounded coding workers

One hundred lessons from building and measuring a thinking MoE and tiny
open models as bounded coding workers for a coding-agent harness: the
ladder, the freeze-the-oracle gate, the redispatch stack, local inference
servers, and a content-tool-call-assist plugin that lets a model that cannot
tool-call natively still drive the loop.

Each lesson is meant to be actionable on its own. They are grouped by theme;
the numbering runs straight through.

## Tool-calling is a format gate, not a size gate

1. Whether a model "works" in a coding agent is decided by one thing first:
   can it emit a tool call in the exact structured shape the harness executes.
   It is a format gate, not an intelligence or size gate.
2. A capable model that emits its tool call *inside its text content* (a fenced
   JSON block, a `<tool_call>` tag) instead of the structured `tool_calls`
   field will end every turn with text and no action, and the loop stalls. The
   model "knows" the call; the harness just never sees it.
3. Before concluding a model is too weak to be an agent, prove the failure is
   capability and not plumbing: read one raw turn and check whether a correct
   call is sitting in the content, unparsed.
4. The cheapest possible probe of "will this model tool-call" is a single
   `curl` to the inference server with the intended system prompt. Do it before
   wiring anything through the full agent.
5. Small open models vary in which JSON shape they emit; do not assume the
   OpenAI/Hermes `{"name","arguments"}` form. Many favor the compact
   `{"tool","args"}` form. Accept both when you parse.
6. "The model works" and "the model passes the task" are different claims.
   Emitting a clean tool-call shape is necessary but not sufficient; producing
   correct arguments against a real file is the harder, separate bar.

## The content-tool-call-assist plugin

7. The right place to fix a content-embedded tool call is a provider shim that
   delegates streaming to the real wire protocol and promotes a content call
   into a structured one before the turn settles — not a patch in the model and
   not a fork of the agent loop.
8. Delegate, don't reimplement: the shim registers a provider whose streaming
   function calls the built-in `openai-completions` streamer and only
   post-processes the result. You inherit every upstream fix for free.
9. Promote at the `done` event, and only when the turn produced no native tool
   call. If the model already tool-called structurally, touch nothing.
10. To promote, append a synthesized `ToolCall` to the settled assistant
    message, set `stopReason` to `toolUse`, and emit the
    `toolcall_start/delta/end` + `done(toolUse)` events the loop expects. The
    rest of the harness then behaves as if the call were native.
11. Keep the model and endpoint env-configurable (`ASSIST_BASE_URL`,
    `ASSIST_MODEL_ID`) so one shim can front any OpenAI-compatible server —
    `mlx_lm.server`, a local inference server, a hosted endpoint — without a
    code change.
12. A loopback inference server needs no real key, but the harness's "models
    require a key" check does. A literal placeholder (`"not-needed"`) satisfies
    the check and is ignored upstream.
13. A provider config exposes exactly the hooks the type declares. An extra
    field (e.g. a second `stream` alias next to `streamSimple`) is an excess
    property; it may be silently ignored at runtime but it is a type error, so
    do not ship it.
14. Make the function signature match the interface it is assigned to. An
    over-strict required parameter where the interface expects an optional one
    is a latent type error that another error on the same object literal can
    mask until you fix the first.

## Parsing a tool call out of free text

15. A regex is the wrong tool for extracting a JSON object from prose. A
    non-greedy match stops at the first inner `}`; a greedy one swallows
    trailing prose. Nested argument objects break both.
16. Use a depth-counting scanner that is string- and escape-aware: track brace
    depth, but ignore braces inside string literals and respect backslash
    escapes. Yield each top-level balanced object.
17. Scan the de-thought text first, then the raw text as a fallback. A model
    can restate a candidate call inside its reasoning; stripping `<think>`
    blocks first avoids promoting the wrong one.
18. Handle a stray or unclosed `<think>` tag: if a closer exists without an
    opener, keep only the text after the last closer. Partial tags are common
    in truncated or streamed output.
19. Coerce both naming conventions at one choke point: accept `name`/`tool` for
    the tool name and `arguments`/`args` for the payload, so the rest of the
    code is convention-agnostic.
20. Accept `arguments` as either an object or a JSON *string*; small models
    emit both. Try to parse a string payload, and fall back to rejecting it if
    it is not an object.
21. Validate shape before promoting: a tool name must be a string and the
    arguments must be an object. A loose check promotes garbage and the loop
    executes nonsense.
22. Borrow a proven parser rather than inventing one. The balanced-brace
    scanner, the thinking stripper, and the `{"tool","args"}` contract came
    straight from an existing local-model harness that had already paid for
    them.

## Forcing / encouraging the call

23. You can pull a small model back to tool-calling with a late system message:
    a short, explicit instruction appended as the last thing before generation.
    It needs no retraining and is model-agnostic.
24. The nudge that works is the one proven on a tiny model: a two-sentence
    think cap, a single worked example of the exact fenced-JSON shape, the real
    tool list with one-line descriptions, and "act by calling a tool; do not
    describe it."
25. Name the real tools in the nudge, pulled from the live tool set in context,
    not a hardcoded list. The model picks from what actually exists this turn.
26. Cap the thinking explicitly ("at most two short sentences, then emit exactly
    one tool call and stop"). Unbounded reasoning is how a small model talks
    itself out of acting and into writing a tutorial.
27. Show, don't just tell: a literal `\`\`\`json {"tool": ..., "args": ...}\`\`\``
    example in the prompt is worth more than a paragraph describing the format.
28. Keep the forcing behind a flag (`ASSIST_FORCE_TOOLS`). It changes model
    behavior and output shape, so it should be opt-in, not a silent default.
29. Inject the nudge by spreading the existing context and appending a message;
    that preserves the context's internal brand/identity. Do not reconstruct
    the context object from scratch.

## Retry is cheap on a tiny model

30. On a tiny model, re-rolling a turn costs a fraction of a second. A retry on
    a prose-only turn is not a real loss, so a bounded retry is a legitimate
    "force," not a hack.
31. A silent retry requires buffering: collect every event of an attempt and
    decide at `done` whether it acted, so a prose-only attempt can be discarded
    and never shown. Live-streaming each token forecloses that choice.
32. A retry must change the sample or it is pointless. At temperature 0 the same
    prose comes out every time; move the seed and/or grow the temperature each
    attempt.
33. Pass the seed through the server's arbitrary sampling-params channel
    (`samplingParams`/extra body fields). It is not a first-class field on most
    option types but OpenAI-compatible servers accept it in the request body.
34. Treat seed and temperature as belt-and-suspenders: if the server ignores
    `seed`, a non-zero temperature step still diversifies the retry. Move both.
35. Keep a temperature *cap*. High temperature corrupts a small model's JSON
    tool calls; past the cap, hold temperature and let only the seed move.
36. Harden the nudge on retry: tell the model its previous reply contained no
    tool call and to reply now with only the fenced JSON. The escalation is
    free and it helps.
37. On the winning attempt, replay the buffered events (promoting the content
    call if needed); on exhaustion, surface the last prose turn as-is rather
    than hanging. Always terminate the stream.
38. Do not retry a hard transport error. An error event is a real failure;
    surface it and stop. Retries are for prose-only turns, not for broken
    requests.

## What tiny models actually do

39. A 2B distill, on a real coding task, tends to write a *tutorial* — a
    well-formed prose explanation with a code block — instead of acting on the
    file. The knowledge is there; the agentic behavior is not.
40. The same distill will emit a clean tool-call shape on a trivial, explicit
    task (write this file with this text). The gap is task realism, not format.
41. A ~2B instruction-tuned model that is drilled on the compact action schema
    emits the exact `{"tool","args"}` fenced block, no prose, first try. The
    prompt contract it was trained/drilled against matters more than parameter
    count.
42. The strong, example-led nudge is what converts a prose-dumping tiny model
    into one that emits the shape. Measure with and without it; the difference
    is the whole point of the shim.
43. Necessary-but-not-sufficient, restated for workers: a tiny model can be made
    to *call* `edit`, but producing the exact `old_string`/`new_string` against
    a real file is a separate capability it may still lack.

## Local inference servers (MLX)

44. `mlx_lm.server`'s `/v1/models` lists everything in the local cache by each
    model's recorded name, not the one model it actually loaded. Do not trust
    that list to tell you what is served.
45. `mlx_lm.server` matches a request's `model` field to the loaded snapshot by
    *path*. Send the absolute snapshot directory as the model id, or you get a
    404 for a model that is plainly in the cache.
46. Resolve a cache snapshot path from the `models--org--name/snapshots/*`
    directory, not the repo id. The repo id is a symlink farm; the server wants
    the concrete snapshot.
47. Verify a new model with a load-and-generate smoke (one short prompt) before
    serving it. A successful import of the arch module does not prove the
    weights load and decode.
48. Confirm the runtime actually supports the architecture: check for the arch
    module by name (e.g. a `gemma4`/`gemma4_text` module) before assuming a new
    model family will load.
49. A model whose architecture is a "conditional generation" (vision-capable)
    variant can still be served text-only if the runtime has a text submodule
    for it. Check rather than assume you need a separate VLM server.
50. Keep each served model on its own port. Two single-process servers on two
    ports run independently; two clients on one port serialize.
51. A single-process MLX server serializes concurrent requests. For a
    comparison run, either accept the serialization or give each arm its own
    server and port.
52. Watch total resident memory when several local models are up at once. A
    thinking MoE plus two tiny 4-bit models fit on a workstation GPU, but it is
    worth a glance before launching parallel runs.

## The managed inference server

53. The managed local server honors a per-request thinking toggle, but only
    when that key is not pinned in its forced server-side settings. Precedence
    is: per-request wins over settings unless the setting is forced.
54. To prove a thinking toggle is honored, do not read docs — send one request
    with thinking off and one with it on and diff the output. Behavior is the
    evidence; configuration is a hypothesis.
55. That server does not compact the conversation; it errors on context
    overflow and pushes the problem back to the client. Compaction is the
    harness's job, not the server's — plan for it.
56. Check prompt caching before blaming latency or nondeterminism on the model.
    A cache that keys on a prefix behaves differently across retries that
    change the seed or a late system message.
57. An admin/loopback auth gate can lock you out of your own local server. The
    fix is a settings flag to skip key verification on loopback, not disabling
    the server's auth wholesale.
58. Record the exact serve command in the repo the moment it works. A
    reproducible one-line recipe (offline flag, model dir, host/port, memory
    guard, concurrency) saves every future spin-up.

## The ladder: measuring a worker

59. Measure a worker on a fixed ladder of rungs with pinned arms, n, scoring,
    and a decision rule *before* any run that decides a change. Exploratory
    runs are screens; preregistered runs are verdicts. Do not blur them.
60. Score by re-running an external test and reading its exit code, never by
    the worker's own "I'm done" message. A model will exit confident on an
    incomplete, self-authored test.
61. The hardest failure to catch is the worker passing its *own* subset of the
    spec. Define "done" with a test the worker did not write, cannot weaken,
    and that covers the whole spec.
62. Freeze the oracle: place the acceptance test as an external, complete,
    unweakenable file, and verify the run by re-running *that* test, not any
    test the worker may have edited.
63. A frozen test only helps if it gives a true signal. A test that passes for
    the wrong reason (or fails on setup noise) gives false hope or false
    despair; validate the oracle itself before trusting its verdict.
64. Keep raw run evidence (traces, stdout, diffs) out of the committed tree;
    publish it as a dated research artifact. The repo keeps the recipe and the
    numbers, not the gigabytes.
65. Separate the worker prompt into one authoritative source and generate the
    shipped templates from it, with a drift test. One prompt, many renderings,
    no hand-edited copies.

## Redispatch and effort

66. When the frozen test fails, re-dispatch the failure to a *fresh* worker
    context rather than letting the same stuck context keep digging. A clean
    slate with the failure in hand beats a long confused transcript.
67. Grow the request temperature per retry (small step, hard cap) and move the
    seed every attempt, so a redispatch explores a new path instead of
    re-running the same greedy decode.
68. Redispatch on timeout, not just on test failure. A worker that stalls is as
    failed as one that produced a wrong edit; both deserve a fresh attempt.
69. Ramp effort: start quick (thinking off, small token budget) and escalate
    (off → medium → high, small → large budget) only as the test keeps failing.
    The test gates the spend, so compute tracks difficulty.
70. "Fail fast, then think longer" is the right default: a short cheap attempt
    catches the easy fixes in sub-second time; only the genuinely hard tasks
    pull in the expensive thinking budget.
71. Slice a long deadline into short fresh-context relays over the cumulative
    workspace, rather than one long attempt. Short attempts fail fast and the
    workspace carries the progress.
72. When you redispatch a failure, hand the worker the *assertion*, not the
    noise. The signal the next attempt needs is the FAILURES section, not a
    scrollback of deprecation warnings.

## The retry-signal bug (a worked example)

73. A retry is only as good as the failure text it carries. A redispatch that
    forwarded the last 1,200 characters of test output forwarded only trailing
    deprecation warnings — no assertion — so the fresh worker had nothing to
    act on.
74. Fix it at the source: run the test with warnings suppressed and a short
    traceback, and extract the FAILURES section deliberately, so the redispatch
    message contains the actual assertion.
75. "Remove the prior reasoning on retry" is a real lever: stale chain-of-
    thought from the failed attempt can mislead the fresh one. Hand over the
    facts and the failure, not the previous thinking.
76. When a mechanism "already exists elsewhere," port the mechanism, not a
    vague memory of it. The existing harness's retry-nudge, stall detection,
    and finish-steer were concrete code worth lifting line for line.

## Reproducing model behavior

77. A thinking model can re-open its reasoning after closing it, giving itself a
    fresh thinking budget each time. Count thinking re-entries; multiple blocks
    in one turn is a signal, not noise.
78. Record per-run diagnostics that explain a pass/fail without re-running:
    thinking level used, token budget, deadline hit, identical-call streak,
    nudge count, stop reason, final-text size. The verdict should be legible
    from the record.
79. Pin the runtime. The ladder requires a recent Python because the code uses
    new syntax; a stray system interpreter will throw a syntax error that looks
    like a bug in the code but is a wrong-interpreter error.
80. `except A, B:` is valid again in current Python (grouped exceptions). If it
    "fails to parse," check the interpreter version before editing the code.

## Honest measurement and reporting

81. Report the result you got, not the one you wanted. "The plugin works but the
    model writes a tutorial instead of acting" is a more useful finding than a
    green checkmark that hides the real gap.
82. Distinguish the three claims every time: the plumbing works, the model emits
    the shape, the model passes the task. Collapsing them is how false progress
    gets reported.
83. When you do not believe a result, re-run it visibly and watch it. A number
    you cannot reproduce in front of yourself is not evidence.
84. "It looks stuck" is often a long deadline, not a hang. Check the configured
    deadline before killing a run; then shorten it if the effort is genuinely
    too slow.
85. Decline to ship a speculative fix. When asked to "fix the model to work
    properly," the honest move was to investigate, find the request was already
    handled correctly, and not open a change that fixes nothing.
86. One good pull request beats several thin ones. Lead its description with a
    table of what changed and why; a sparse summary buries the work.

## Process and hygiene

87. Build test-first: show the new test failing before you make it pass. A
    mechanism you cannot watch fail is a mechanism you cannot trust to pass for
    the right reason.
88. Stage explicit paths and commit only your own files. In a tree where several
    agent sessions may run at once, `git add -A` stomps on other sessions'
    work.
89. Keep the changelog current as work lands, not at release time. A commit
    that changes what a user installs, runs, or reads carries its changelog
    entry in the same commit.
90. Respect document caps as a forcing function. Over the cap means a linked
    research note is owed, not that the prose gets silently trimmed.
91. Hydrate missing dev-dependencies with the sanctioned install path (ignore
    lifecycle scripts) and stage only your real change, never the incidental
    lockfile churn, unless the lockfile change is the point.
92. Run ad-hoc scripts from a scratch directory, pass downloaded or
    untrusted paths as arguments, and run with an isolated interpreter.
    An interpreter loads modules from the script's own directory; a planted
    file can hijack an innocent import.
93. Put throwaway outputs in the session scratchpad, not the project tree or a
    shared temp dir. The scratchpad is isolated, per-session, and never shows
    up as spurious repo changes.
94. Keep an external constraint (such as a term that must never appear in any
    output) in persistent memory, and scrub it from everything you produce:
    commits, docs, reports, snippets.

## Patterns worth stealing from a working local-model harness

95. Prefer a simplified action schema for small models: one tool per reply, a
    single fenced JSON block, a compact `{"tool","args"}` shape. Less surface
    area means fewer ways for a small model to go wrong.
96. Route by understanding, not an ever-growing keyword regex. Let the model
    classify intent; a regex that grows a case per phrasing is the anti-pattern
    that rule exists to stop.
97. Shape output by prompting, not post-processing. If the model emits an
    unwanted form, fix the prompt so it stops — do not strip the output after
    the fact. (The content-call promotion is the deliberate exception: it
    recovers a *correct* call the harness could not otherwise see.)
98. Ground answers in retrieved docs, not canned strings, and keep the whole
    loop runnable offline. Local model plus bundled docs needs the network only
    once, to warm a cache.
99. Gate output with real oracles: run the code, check the value, check the
    types. A reply never ships a result the harness has not independently
    verified.
100. Solve at the root. If a fix feels like whack-a-mole — a regex per phrasing,
     a strip per bad output, a retry that carries no signal — stop and fix the
     real cause. Every durable lesson here came from refusing the band-aid.

## Addendum — measured this session

- **Don't strip the host's native tool field to "clean up" the prompt.** The
  same transcript tools render tool-*result* turns and gate execution, so
  removing them breaks the loop the moment a result enters the history — the
  model emits an empty turn and dies. A prettier, smaller prompt measured 0/15
  where the native (ugly, run-on) tool block measured 5/15. The cosmetic defect
  was real; it was not the cause of failure. See
  [research/2026-10-19-small-model-tool-presentation.md](docs/superpowers/research/2026-10-19-small-model-tool-presentation.md).
  The ladder earned its keep: it caught a plausible optimization that was a
  regression.

- **Fail fast *and* fail loud.** Fail fast: start on a small budget (thinking
  off, ~2k tokens) and escalate only as a frozen test keeps failing, so compute
  tracks difficulty — the opposite of handing every rung 16k up front (lesson
  70). Fail loud: a run that goes quiet is a bug, not patience. A worker turn
  stalled ~7 minutes on a blocking tool call with the deadline not biting, and
  nothing surfaced it — the only tell was oMLX going idle. Make failure and
  stalls obvious: stream every rung's trace on screen (a ladder run without its
  trace visible is a bug), bound blocking tools, and carry the real assertion
  into a retry (lessons 72–75), never a silent hang or a blind tail.

## Addendum — mediation, crutches, and self-narrowing (2026-10-21)

- **The worker narrows its own test and calls it done — and a prompt fixes it.**
  The sharpest form of lesson 61: on the two rungs the 6-bit "could not" do bare
  (4 and 5, 0/1), the trace showed it was not incapable and did not cheat — it
  ran the whole `test_export.py`, saw several failures, then narrowed pytest to
  the single function it was fixing (`...::test_export_appends_totals_row`),
  passed that one, and self-certified on the subset ("that test passes"). A
  generic, task-independent nudge — "run the whole test file, make **every** test
  in it pass, never a single `::test_function`, before you finish" — flipped both
  to PASS un-mediated (rung 4: full 3-file refactor, 53 s; rung 5: decoy
  untouched, 90 s), with no frozen test and no redispatch. Read *what the worker
  ran* before concluding a capability wall; the failure was a stopped-early habit,
  not a missing skill.

- **Mediation is a completeness gate, not a capability crutch.** Bare (no frozen
  test, no redispatch) the 6-bit scored 6/12 — and the pattern is the lesson: it
  passes rung 12, the one *designed* to overflow context, and fails the
  *coordination* rungs (4, 5, 6, 9, 10, 11 — multi-file refactors, a trap row, an
  old phase to keep working). It fails on finishing the job, not on difficulty.
  Mediation left rung 12 alone (the model already clears it) and flipped 10 and 11
  from fail to 3/3. So the gate recovers completeness failures; it does not prop
  up incapacity, and reporting it as capability would be the real crutch —
  which is why you run and report the un-mediated pass too.

- **External-test-and-redispatch is CI, not a crutch — judged by where the test
  comes from.** A mediated PASS transfers to the real world when the acceptance
  test pre-exists (a failing repro, a ticket's criteria, an existing suite) or is
  cheap and trustworthy to write — and never when it was authored by the worker
  or is thin enough to game. Keep held-out checks the worker never optimizes
  against (the hidden oracle is a *superset* of the frozen test it sees), keep the
  gate uneditable, bound the redispatch, and gate the irreversible. The honest
  boundary: where "done" is subjective, no oracle exists and the number says
  little. See
  [research/2026-10-21-mediation-real-world.md](docs/superpowers/research/2026-10-21-mediation-real-world.md).

- **"Self-certifies against a subset" has two forms, and a prompt fixes both.**
  The worker fails by grading itself against less than the whole — either a
  subset of the *tests* (runs the file, then narrows to one `::test_function` →
  the rungs 4/5 failures, fixed by the v8 "run the whole file, pass every test"
  nudge) or a subset of the *spec* (makes every visible test pass but skips a
  spec requirement no visible test checks → rung 9's **Phase-4 id miss**: the
  spec says "each complaint gets a unique, automatically-assigned id", no visible
  test checks id distinctness, so the worker left `id = 0`). The v9 nudge — "the
  spec is the full contract; implement every requirement, like unique ids, even
  when no visible test checks it" — flipped rung 9's hidden oracle to green. The
  surprise: the Phase-4 id miss was the canonical case that *motivated* the frozen
  oracle, and it turned out prompt-fixable. So prompt hardening and the frozen
  oracle are **complementary layers**, not either/or — the prompt lifts the floor
  (fewer self-narrowed exits), the frozen oracle is the backstop for when the
  prompt does not take. Measured: bare un-mediated ladder went 6/12 → 11/12 (v8)
  with 4/5/6/10/11 flipping, and rung 9 then closed under v9.
