# Phase 4 — Resolve and Reopen

- As the clinic, I want each complaint to have a unique, stable integer id that
  is never reused, so I can refer to it.
- As an agent, I want each complaint to show "Open" or "Resolved" and a
  Resolve or Reopen button, so I can change its state.
- As a visitor, I want resolving and reopening to redirect (303) and never
  reorder the board.

**Acceptance.**

- `Complaint` also has `id: int` and `status: str`, and `Complaint(agent_name,
  text)` still constructs positionally: each new complaint's `id` is unique and
  greater than every earlier one, `status` starts as `open`, and how that is
  achieved is the implementer's choice.
- The seeded complaints have distinct ids.
- Each card shows `Open` or `Resolved` and a button that posts to its route.
- `POST /complaints/{id}/resolve` marks that complaint resolved and answers 303
  with `Location: /complaints`; the board then shows `Resolved`.
- `POST /complaints/{id}/reopen` marks it open and answers the same way.
- Resolving or reopening never changes the board's order.
- Phases 1 to 3 still pass.
