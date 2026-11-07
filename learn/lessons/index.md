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

Medium and Hard are next; their lessons land as the ladder reaches them.
