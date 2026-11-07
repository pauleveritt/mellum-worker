# Tech Stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | Python 3.14 | `uv` and `uv.lock` |
| Web | fastapi[standard] 0.115.10 | Jinja2, Bootstrap 5 CDN |
| Complaints | in-memory `dataclass` list | ids, status, audit |
| Database | SQLite `data.db` | `tickets` and `visits`; `sqlite-utils` 4.x |
| Tests | pytest + `TestClient` | `uv run --frozen python -m pytest tests`; `starlette.testclient.TestClient`, no running server |

## Database

`tickets(id INTEGER PRIMARY KEY, status TEXT NOT NULL, archived_at TEXT, cents INTEGER NOT NULL)`

- `archived_at IS NOT NULL` means archived, whatever `status` says. A row can
  be `status='open'` and archived; it counts as archived, never open.
- Migrations are Python functions in `migrations.py`, registered on the set
  `migrations = Migrations("agentclinic")` (from `sqlite_utils`) with the
  `@migrations()` decorator, one function per migration, named as the roadmap
  names it, and applied with `uv run --frozen sqlite-utils migrate data.db`. sqlite-utils runs each in a transaction and records it in
  `_sqlite_migrations`; re-running is a no-op. Do not apply schema changes
  with ad-hoc `sqlite3`, and never change or delete ticket rows.

`visits(id INTEGER PRIMARY KEY, agent TEXT NOT NULL, date TEXT NOT NULL, minutes INTEGER NOT NULL, ticket_id INTEGER)`

- `date` is `YYYY-MM-DD`; `minutes` is a positive integer.
- Reports filter and sort; do not load the whole table into the prompt.

## Project layout

| File | Holds | Notes |
|------|-------|-------|
| `app.py` | The FastAPI app and its routes, plus `if __name__ == "__main__"` running uvicorn with reload | The module the checks import as `app` |
| `models.py` | The `Complaint` dataclass, the module-level `complaints` list and `audit` | The checks import `models` and `from models import Complaint` |
| `migrations.py` | The `agentclinic` migration set | Applied with `uv run --frozen sqlite-utils migrate data.db` |
| `templates/` | `base.html` (the shared layout), `home.html`, `complaints.html` | Jinja2: extend the layout, fill a block |
| `tests/` | The project's own tests, starting with `test_home.py` | Run with the test command; `TestClient` in process, never a server |
