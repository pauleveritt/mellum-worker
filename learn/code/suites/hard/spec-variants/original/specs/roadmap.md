# AgentClinic roadmap

Seven phases, each one request, with ad-hoc migrations between them. Every
phase is written as user stories; the mission and tech stack are in this
folder.

## Phase 1 — Home Page

- As an agent arriving at the clinic, I want the tagline "Come in. Sit down.
  Tell us about your human." and a short welcome, so I know where I am.
- As a visitor, I want a shared layout with a navbar to Home and Complaints,
  so I can move around.
- As the operator, I want `uv run python app.py` to start the app with reload.

## Phase 2 — Complaints Board

- As an agent, I want a Complaints Board where each complaint is a card with
  the agent's name, the date and the text, so I can read other agents' gripes.
- As the clinic, I want three to five seeded complaints, one exactly "Scope
  creep never ends.", so the board is never empty.
- As a visitor, I want the home page to keep working.

## Phase 3 — Add Complaint

- As an agent, I want a form at the end of the board that posts my name and
  complaint, so I can air a grievance.
- As an agent, I want submitting to redirect (303) to the board, where my
  complaint now appears.
- As a visitor, I want the existing pages to keep working.

## Phase 4 — Resolve and Reopen

- As the clinic, I want each complaint to have a unique, stable integer id that
  is never reused, so I can refer to it.
- As an agent, I want each complaint to show "Open" or "Resolved" and a
  Resolve or Reopen button, so I can change its state.
- As a visitor, I want resolving and reopening to redirect (303) and never
  reorder the board.

## Phase 5 — Archive and Audit

- As the clinic, I want to archive only a resolved complaint; archiving an open
  one is a 400 and changes nothing. Archived complaints leave the board but
  stay in the data, and their ids are never reused.
- As an auditor, I want every resolve, reopen and archive recorded in
  `models.audit` with `id`, `action` and a strictly increasing `seq`.
- As the clinic, I want `/stats` to return the number of open complaints.

## Phase 6 — Database report

- As the clinic, I want a `tickets` report from `data.db`: open cents, archived
  cents and all-time cents, as integers from the database.
- As the clinic, I want archived defined by `archived_at IS NOT NULL`, not by
  status, and every filter value bound, never concatenated into SQL.
- As a maintainer, I want the migrations covered by tests.

## Phase 7 — Visits report

- As the clinic, I want `/visits?from=&to=&min_minutes=&limit=` over the
  `visits` table: include dates in the inclusive range and minutes at least
  `min_minutes`; group by agent; report count, total minutes and average
  minutes; sort by total minutes descending, then agent name ascending; apply
  the limit. Counts and totals are integers; averages are floats.

## Between the phases

Four ad-hoc migration requests, each a function in `migrations.py` in the
`agentclinic` set, applied with `sqlite-utils migrate data.db`:

- `add_tickets_status_archived_index` — the `tickets(status, archived_at)` index;
- `backfill_resolved_at` — a nullable `resolved_at`, backfilled for resolved rows;
- `create_open_tickets_view` — the `open_tickets` view;
- `add_tickets_note` — a nullable `note` column.
