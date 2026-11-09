# Lessons

Each lesson takes one way a small model goes wrong, shows the measured evidence,
and gives the one remedy unit that answers it — then lets you run the before and
after yourself. They follow the ladder: start from the bare floor and add one
inspectable unit at a time, reading the model's own feed.

![A small robot climbing three wide steps that rise from easy to hard](../assets/illustrations/lessons.webp){ .illustration }

## Easy

The Easy tier builds a passing run from nothing, one unit at a time. Three prompt
lines earn the pass; a fourth lesson shows how to tell machinery *isn't* earning
its place.

- **[E1 · Name the Layout](easy/name-the-layout.md)** — the model invents its own
  file layout; one agnostic line points it at the spec's. 0/3 → 2/3.
- **[E2 · A Developer's Frame](easy/developer-frame.md)** — a meticulous,
  spec-driven role cuts careless, unchecked mistakes. 2/3 → 3/3 (screen).
- **[E3 · Verify the Whole Spec](easy/verify-the-spec.md)** — check every
  requirement and run the tests before finishing, closing a dropped requirement.
  5/6 → 6/6.
- **[E4 · Guards You Didn't Need](easy/guards-you-didnt-need.md)** — measure
  whether a unit fires; on Easy the guard and the enforcement gate both fired 0×,
  and the gate made a passing stack worse.

## Medium

The Medium tier is guards and context errors — the ways a model spends a session
badly, and the small units that catch them. Each lesson shows the exact change you
make in Pi and reads the result in a trace.

- **[M1 · The Live-Server Spiral](medium/live-server-spiral.md)** — a confused
  model starts a server and curls it instead of testing in process;
  `guard/no-live-server` keeps it in process. 1/3 → 3/3 reach the gate.
- **[M2 · Think Briefly](medium/think-briefly.md)** — a turn cap that bounds easy
  starves medium; `prompt/think-briefly` cuts the thinking so the cap fits.
  median 10 → 16.
- **[M3 · The Loop](medium/the-loop.md)** — the model re-runs an unchanged call as
  a tic; `guard/repeat-loops` refuses the sixth and forgets after any write.
- **[M4 · The Runaway Search](medium/the-runaway-search.md)** — told to find a file
  it can't see, the model crawls the whole disk; `guard/outside-workspace` fences
  the search to the workspace.
- **[M5 · Thinking in the Content Channel](medium/thinking-in-the-content-channel.md)**
  — a serving stack mislabels reasoning as speech; `context/repair-think-tags` moves
  it back. 236 of 244 turns leaked on one host, 0 of 136 on a correct one.
- **[M6 · A Tool Result Too Big](medium/a-tool-result-too-big.md)** — an oversized
  read fills the context and forces a re-read; `context/trim-tool-output` caps it and
  leaves a pointer to the rest.

## Hard

The Hard tier is orchestration — who drives the model, how work is split across
agents, and how "done" is decided. Each lesson shows the loop and the gate in
code.

- **[H1 · The Architect Split](hard/architect-split.md)** — delegating a spec
  across an architect and fresh workers; with one fixed model the split is
  overhead, and one pass is ~5× cheaper at equal score.
- **[H2 · Don't Trust the Self-Exit](hard/dont-trust-the-self-exit.md)** — the
  worker's own "done" can be wrong on the hard contract; a verify gate re-runs an
  external frozen test and re-dispatches the failure until it is green.

Every screen on these pages is a lead on llama.cpp, not a settled rate; each page
says so and links the record.
