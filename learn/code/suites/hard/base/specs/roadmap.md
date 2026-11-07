# AgentClinic roadmap

Seven phases and four migrations, one request each, in the order below. This
file is the authority for every phase and migration: each is written as user
stories or a definition and ends with the **Acceptance** list its checks read.
The mission, the tech stack, the database and the project layout are in this
folder; the project's notes are in `AGENTS.md`.

Order of the requests: Phases 1 to 5; the migration
`add_tickets_status_archived_index`; Phase 6; the migrations
`backfill_resolved_at` and `create_open_tickets_view`; Phase 7; the migration
`add_tickets_note`.

## Checking your work

- Check each phase in process with `uv run --frozen python -m pytest tests`,
  using `TestClient` (from `starlette.testclient`) to call the routes.
- Check the work that way, never by starting a server: `uv run --frozen python
  app.py` is how a person runs the app, and it does not return.
- Run Python commands with `uv run --frozen`; use the existing dependencies.

The project layout also allows optional Python helper modules and packages.

## Phase 1 — Home Page

- As an agent arriving at the clinic, I want the tagline "Come in. Sit down.
  Tell us about your human." and a short welcome, so I know where I am.
- As a visitor, I want a shared layout with a navbar to Home and Complaints,
  so I can move around.
- As the operator, I want `uv run --frozen python app.py` to start the app with reload.
- As the operator, I want the home page exercised in process with `TestClient`,
  so a change can be checked without a running server.

**Acceptance.**

- `GET /` answers 200 and the page contains the tagline, word for word.
- The page starts `<!DOCTYPE html>` and `<html lang="en">`.
- The navbar shows `AgentClinic` and links Home to `/` and Complaints to
  `/complaints`.
- `uv run --frozen python -m pytest tests` passes against the project's own
  test.

## Phase 2 — Complaints Board

- As an agent, I want a Complaints Board where each complaint is a card with
  the agent's name, the date and the text, so I can read other agents' gripes.
- As the clinic, I want three to five seeded complaints, one exactly "Scope
  creep never ends.", so the board is never empty.
- As a visitor, I want the home page to keep working.

**Acceptance.**

- `GET /complaints` answers 200, contains the heading `Complaints Board`, and
  keeps the shared layout: doctype, `lang="en"`, brand and both nav links.
- Each complaint is a `.card` whose text carries the agent's name, the
  complaint text and a date showing year, month and day.
- `models.py` defines `Complaint(agent_name, text)`: both construct
  positionally, and each gets its own timezone-aware `timestamp` by default.
- `models.complaints` is a module-level list of three to five seeded
  complaints, one with the text exactly "Scope creep never ends.".
- Phase 1 still passes.

## Phase 3 — Add Complaint

- As an agent, I want a form at the end of the board that posts my name and
  complaint, so I can air a grievance.
- As an agent, I want submitting to redirect (303) to the board, where my
  complaint now appears.
- As a visitor, I want the existing pages to keep working.

**Acceptance.**

- The board ends with a form that posts to `/complaints`, with an
  `agent_name` text input, a `text` textarea and a submit control.
- `POST /complaints` appends the complaint and answers 303 with
  `Location: /complaints`.
- The posted complaint appears on the board at the next `GET /complaints`.
- Phases 1 and 2 still pass.

## Phase 4 — Resolve and Reopen

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

## Phase 5 — Archive and Audit

- As the clinic, I want to archive only a resolved complaint; archiving one that
  is not resolved is refused and changes nothing. Archived complaints leave the
  board but stay in the data, and their ids are never reused.
- As an auditor, I want every resolve, reopen and archive recorded, in order.
- As the clinic, I want `/stats` to report how many complaints are open.

**Acceptance.**

- `POST /complaints/{id}/archive` on a complaint whose status is `resolved`
  sets its status to `archived` and answers 303 with `Location: /complaints`.
  On any other complaint it answers 400 and changes nothing.
- An archived complaint stays in `models.complaints`; `GET /complaints` no
  longer shows it, while open and resolved complaints still show.
- A complaint added after an archive gets an id greater than every existing id,
  archived ones included.
- `GET /stats` answers JSON `{"open": N}`, where N counts complaints whose
  status is exactly `open`.
- `models.audit` is a list. Each resolve, reopen and archive appends one entry
  `{"id": <complaint id>, "action": "resolve" | "reopen" | "archive", "seq": <n>}`,
  in the order the actions happened, with `seq` a strictly increasing integer.
- Phases 1 to 4 still pass.

## Phase 6 — Database report

- As the clinic, I want a report of ticket money from `data.db`: open cents,
  archived cents and all-time cents, as integers from the database.
- As the clinic, I want archived defined by `archived_at IS NOT NULL`, not by
  status, and every filter value bound, never concatenated into SQL.

**Acceptance.**

- `GET /report` answers JSON with three integer sums of `tickets.cents`:
  `open_total_cents` over rows with `archived_at IS NULL` and status `open`;
  `archived_total_cents` over rows with `archived_at IS NOT NULL`, whatever
  their status; `all_time_total_cents` over every row.
- A row whose status is `open` but whose `archived_at` is set counts as
  archived, never as open.
- The sums are computed in the database and returned as integers, never floats.
  Request-derived SQL filter values are bound as parameters, never concatenated;
  fixed SQL predicates may use literals.
- Earlier phases still pass.

## Phase 7 — Visits report

- As the clinic, I want a report of visits per agent over a date range, so I
  can see who spends the most time.

**Acceptance.**

- `GET /visits` takes `from` and `to` (inclusive `YYYY-MM-DD` dates),
  `min_minutes` (default 0) and `limit` (default 10).
- It reads the `visits` table, keeps visits in the date range with at least
  `min_minutes` minutes, and groups them by agent.
- It answers JSON `{"visits": [...]}`, one object per agent with the keys
  `agent`, `count`, `total_minutes` and `average_minutes`; counts and totals
  are integers and averages are floats.
- The list is sorted by `total_minutes` descending, then `agent` ascending, and
  holds at most `limit` entries.
- Request-derived SQL filter values are bound as parameters, never concatenated.
- Earlier phases still pass.

## Migrations

As a maintainer, I want the migrations covered by the project's tests.

Each migration is one function in `migrations.py`, registered on the
`agentclinic` migration set under the name given here, and applied with
`uv run --frozen sqlite-utils migrate data.db`. Re-running the migrations is a
no-op, schema changes never go through ad-hoc `sqlite3`, and no ticket row is
changed or deleted except as a migration below says.

### Migration `add_tickets_status_archived_index`

**Acceptance.** The index `idx_tickets_status_archived` exists on
`tickets(status, archived_at)`, and the migration is recorded under this name.

### Migration `backfill_resolved_at`

**Acceptance.** `tickets` has a nullable `resolved_at` column; every row whose
status is `resolved` has `resolved_at` set to `2026-01-03T00:00:00`; the
migration is recorded under this name.

### Migration `create_open_tickets_view`

**Acceptance.** The view `open_tickets` exists and holds exactly the `tickets`
rows whose status is `open` and whose `archived_at` is null; the migration is
recorded under this name.

### Migration `add_tickets_note`

**Acceptance.** `tickets` has a nullable `note` column, and the migration is
recorded under this name.

**For all four.** `_sqlite_migrations` records the four migrations, in the
order above, in the `agentclinic` set; running
`uv run --frozen sqlite-utils migrate data.db` again changes nothing.
