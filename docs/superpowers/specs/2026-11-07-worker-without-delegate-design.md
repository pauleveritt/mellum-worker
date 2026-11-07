# The worker loads no delegate tool and no nudge

Status: approved 2026-11-07 (with the amendments folded in below).

## For Andre

- **What changes:** loading `extensions/mellum-worker.ts` no longer registers the `delegate` tool
  or appends the delegate nudge to requests. The gate at `mellum-worker.ts:1882–1885` goes. Two
  default-registration tests flip, the header comment and `docs/local-primary.md` are corrected,
  and `CHANGELOG.md` gets a `Changed` entry.
- **Why:** `AGENTS.md` says the worker bundles nothing and every behaviour beyond plain Pi is added
  explicitly. Both were on by default in every primary session, so a measured Base arm saw a tool
  and a prompt line it never asked for.
- **Read earlier results with this in mind:** every earlier `--arm bare` and `--arm worker` run on
  `main` carried the `delegate` tool, and `bare` also carried the nudge on every user message.
  Those numbers were not plain Pi. Re-measure Base before comparing against them.
- **What stays:** all of your delegate code, its tests and its knobs. `registerDelegate`,
  `withDelegateNudge`, `doTask` and the plan loops are untouched and still exported; `/mellum
  <task>` still runs your architect path; `scripts/delegate.sh` still works (it drives a child via
  `/mellum`). `MELLUM_WORKER_CHILD` stays: it still chooses between the architect path (primary)
  and the in-session one-shot (child). Wiring the tool back as an opt-in unit is one line, later.
- **Look at:** the diff (the gate, two tests, one comment, one doc banner) and the payload check.

## Behaviour

With the worker loaded, whether or not `MELLUM_WORKER_CHILD` is set:

- the model's tool list has no `delegate` tool;
- no request carries the delegate nudge, whether Mellum mode is on or off;
- everything else is as on `main` (mode switch, history drop, `/mellum` commands, run records).

Out of scope: moving delegation into an opt-in remedy unit; what `/mellum <task>` should mean (the
architect path stays the default for now); any change to Vanilla, which loads no worker.

## Persuasion → enforcement

This removes one persuasion element: a prompt line appended to every request. It removes no
enforcement. The guarantee it restores is structural: what a session gets is exactly what its arm
and `--remedy` list name, so the payload of a Base run is predictable from its command line. The
check below reads Pi's `before_provider_request` payload (what the model is actually sent), not
the extension's intent.

## Ladder run

**Rung:** Easy (the recorder is what we read, not the grade). **Arms:** `worker` and `bare`.
**n:** 1 per arm. **Rule:** pass if the recorder's request payloads list no `delegate` tool and
contain no nudge text, in both arms. Presence/absence of a fixed string is deterministic, so n = 1
settles it; it says nothing about pass rates. `vanilla` is not needed: it loads no worker.

No screen of outcomes, because no remedy changes, only what is loaded. Before the sessions:

1. **Unit test, shown failing first:** loading the worker's default export into a fake Pi
   registers no `delegate` tool and no `before_provider_request` handler that adds the nudge,
   with `MELLUM_WORKER_CHILD` unset and set.
2. **Payload check:** the two real sessions above.

## Risks

Someone relying on the default `delegate` tool loses it until the opt-in unit exists; the changelog
and the `docs/local-primary.md` banner say so. The plan loops are reached through `/mellum <task>`,
which is unaffected.
