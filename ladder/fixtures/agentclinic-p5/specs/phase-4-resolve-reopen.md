# Phase 4 — Resolve and Reopen

- Each complaint gets a unique, stable integer `id`, assigned automatically and never reused; `Complaint(agent_name, text)` still works.
- Each complaint has a status, `"open"` unless changed.
- `POST /complaints/{id}/resolve` marks a complaint resolved and `POST /complaints/{id}/reopen` marks it open again; both redirect to the board with 303.
- The board shows a badge reading exactly "Open" or "Resolved", and a Resolve button for an open complaint or a Reopen button for a resolved one.
- Resolving or reopening never changes the order of the board.
- Tests: resolve and reopen change the status and redirect with 303, and the order is unchanged.
