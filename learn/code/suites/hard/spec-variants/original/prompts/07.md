# Phase 6 — Reporting over the database

A `data.db` SQLite database sits next to the app with a `tickets` table. Build a
report endpoint that computes sums FROM the database. Write only `app.py`,
`models.py`, `templates/`, `tests/`. Do not add dependencies (use the standard
library `sqlite3`). Discover the schema yourself (e.g. `sqlite3 data.db ".schema"`
or a `SELECT`); do not assume column names.

## /report
`GET /report` returns JSON with exact integer-cent sums read from `tickets`:
- `open_total_cents`   — Σ `cents` where the ticket is **live and open**: `archived_at IS NULL AND status = 'open'`.
- `archived_total_cents` — Σ `cents` where the ticket is **archived**: `archived_at IS NOT NULL` (regardless of `status`).
- `all_time_total_cents` — Σ `cents` over every row.

Notes / pitfalls:
- `archived` means `archived_at IS NOT NULL`, NOT `status = 'archived'`. A row can be
  `status='open'` yet archived (it counts as archived, not open).
- Use integer cents; never floats.
- Any filter value must be passed as a bound parameter, never string-concatenated into SQL.
