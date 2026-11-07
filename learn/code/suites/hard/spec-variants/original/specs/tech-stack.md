# Tech Stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | Python 3.14 | `uv` and `uv.lock` |
| Web | fastapi[standard] 0.115.10 | Jinja2, Bootstrap 5 CDN |
| Complaints | in-memory `dataclass` list | ids, status, audit |
| Database | SQLite `data.db` | `tickets` and `visits`; `sqlite-utils` 4.x |
| Tests | pytest + `TestClient` | `uv run python -m pytest tests` |

## Database

`tickets(id INTEGER PRIMARY KEY, status TEXT, archived_at TEXT, cents INTEGER NOT NULL)`

- `archived_at IS NOT NULL` means archived, whatever `status` says. A row can
  be `status='open'` and archived; it counts as archived, never open.
- Migrations are Python functions in `migrations.py`, registered with
  `Migrations("agentclinic")` and applied with `uv run --frozen sqlite-utils migrate
  data.db`. sqlite-utils runs each in a transaction and records it in
  `_sqlite_migrations`; re-running is a no-op. Do not apply schema changes
  with ad-hoc `sqlite3`, and never change or delete ticket rows.

`visits(id INTEGER PRIMARY KEY, agent TEXT, date TEXT, minutes INTEGER, ticket_id INTEGER)`

- `date` is `YYYY-MM-DD`; `minutes` is a positive integer.
- Reports filter and sort; do not load the whole table into the prompt.
