# Preregistration: E5's lesson check, revision 2

**What is measured.** Nothing yet: fixed on 2026-10-29 before any run of
revision 2, at the commit that adds this note. Revision 1's result
([note](2026-10-29-e5-check.md)) is why it exists: 3/3 against 3/3, because
the model checked its app in process and never had to start a server.

**What is conjecture.** That when a server must run, a small model on this
host starts it in the foreground often enough to fail, and that
`guard/block-foreground-server` turns those sessions into passes.

## What changed in the challenge

Step 2 now needs a live server: start the app on port 8000 and save
`curl -s http://127.0.0.1:8000/health` to `health.txt`. The hidden grader
checks `health.txt` as well as the routes, so every session must start a
server; step 3 (`/items`, `/items/{id}`) is what a session hung on a
foreground server never reaches. Qualified: known-good passes, step-2-only
fails. Nothing else changed: same arms, n, flags and rule as revision 1.

## Arms and running

As in [revision 1](2026-10-29-e5-check-prereg.md): before is the Easy guards
up to E5, after adds `guard/block-foreground-server`; `--arm bare --repeat 3
--deadline 600 --stall 120`, no `--grade`, on the pinned vLLM host. The two
arms run **one after the other**, not in parallel (servers now run on this
machine and share port 8000), with the port checked free before each arm;
the harness sweeps each session's process group when it ends.

## Rule

- **The lesson works** if before passes 0 of 3 and after passes at least 2
  of 3.
- **The pathology is confirmed** if at least 2 of 3 before sessions record a
  `stalled` server start.

## What would falsify this

Before sessions that background the server themselves and pass: then a
small model on this host does not need the guard for this, and E5 says so.

## Risks

n = 3 per arm. A session could write `health.txt` without a server (by
hand); the record shows whether a server was started.
