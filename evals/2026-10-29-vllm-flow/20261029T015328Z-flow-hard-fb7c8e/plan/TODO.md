## North Star
Add visits report endpoint and nullable note column to tickets.

- [ ] `GET /visits` takes `from`, `to` (inclusive ISO dates), `min_minutes` (default 0) and `limit` (default 10)
- [ ] Group the `visits` table by agent for visits in range with at least `min_minutes`
- [ ] return `{"visits": [{"agent", "count", "total_minutes", "average_minutes"}]}`
- [ ] sorted by total minutes descending then agent name ascending, and limited
- [ ] Counts and totals are integers, averages are floats
- [ ] Add a migration to `migrations.py` in the `agentclinic` set
- [ ] Name it `add_tickets_note`
- [ ] add a nullable `note` column to `tickets`
- [ ] Apply it with `uv run --frozen sqlite-utils migrate data.db`
- [ ] re-running must be a no-op
- [ ] Keep every existing route and test working
