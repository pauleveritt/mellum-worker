## North Star
Build report endpoint and required database migrations for AgentClinic.
- /report
- open_total_cents
- archived_total_cents
- all_time_total_cents
- archived_at IS NULL AND status = 'open'
- archived_at IS NOT NULL
- Σ cents over every row
- archived means archived_at IS NOT NULL, NOT status = 'archived'
- Use integer cents; never floats.
- Any filter value must be passed as a bound parameter, never string-concatenated into SQL.
- backfill_resolved_at
- create_open_tickets_view
- uv run --frozen sqlite-utils migrate data.db
- re-running must be a no-op
- Add a migration to migrations.py in the agentclinic set
- Write only app.py, models.py, templates/, tests/
- Do not add dependencies (use the standard library sqlite3)
- Discover the schema yourself
