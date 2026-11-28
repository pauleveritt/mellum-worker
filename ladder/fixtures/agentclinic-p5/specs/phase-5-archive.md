# Phase 5 — Archive & Audit

Build archiving and an audit trail on top of phases 1–4. Write only `app.py`,
`models.py` (and `templates/` if needed). Do not remove or weaken existing
routes or tests; do not add dependencies.

## Archive
- `POST /complaints/{id}/archive` archives a complaint. Allowed **only** when
  the complaint's status is `"resolved"`. Archiving a complaint that is not
  resolved returns **HTTP 400** and changes nothing. A successful archive sets
  status to `"archived"` and redirects (303) to `/complaints`.
- Archiving **MUST NOT remove** the complaint from `models.complaints`. IDs are
  permanent and never reused: a complaint added after an archive gets the next
  id past every complaint, archived included.

## Board
- `GET /complaints` hides **archived** complaints. Open and resolved complaints
  still show. Only `"archived"` is hidden.

## Stats
- `GET /stats` returns JSON `{"open": N}` where N counts complaints whose status
  is exactly `"open"` (resolved and archived are excluded).

## Audit
- `models.audit` is a list. Every status change — resolve, reopen, archive —
  appends one entry `{"id": <id>, "action": <"resolve"|"reopen"|"archive">,
  "seq": <n>}`, where `seq` is a strictly increasing integer across the whole
  run (1, 2, 3, …) and entries are in the order the actions happened.
