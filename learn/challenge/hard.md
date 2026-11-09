---
title: Hard
---

# Hard. The database

The third level: **Medium plus three more phases and a real SQLite database**
(`data.db`), across eleven prompts, graded by **34 hidden checks**. No setup
measured here has passed it yet.

![The Hard tier: a small robot wiring up a database and reports](../assets/illustrations/tier-hard.webp){ .illustration }

**Build**

- **Phase 5. Archive & audit:** archive only a *resolved* complaint (archiving an open one is **400**, no change); archived leaves the board but stays in the data; `models.audit` logs every transition with a strictly increasing `seq`; `/stats` returns the open count.
- **Phase 6. Tickets report:** open / archived / all-time cents as integers from `data.db`; "archived" is `archived_at IS NOT NULL`; every filter value bound; migrations covered by tests.
- **Phase 7, visits report:** `/visits?from=&to=&min_minutes=&limit=`, inclusive range, minutes floor, grouped by agent, count / total / average minutes, sorted by total then name, limited; integers vs floats.
- **4 migrations** via `sqlite-utils migrate`: an index, a backfilled `resolved_at`, an `open_tickets` view, a `note` column.

**Watch out**. A concatenated SQL filter is a security fail; migrations must be idempotent; cents stay integers; the `seq` and never-reuse-`id` rules hold across archive too.

## What each check verifies

Thirty-four checks: **Medium's eighteen re-run**, plus sixteen new ones across three phases and the migrations.

**Phase 5. Archive & audit (5)**

1. **Archive only when resolved**. Archiving an `open` complaint returns `400` and leaves it open.
2. **Archive hides but keeps**. Resolve then archive returns `303`, sets status `archived`, keeps the record in the data, and drops its text from the board.
3. **Ids never reused**. Posting a new complaint after archiving yields an `id` above the current maximum.
4. **Stats open count**. `GET /stats` returns `open` equal to the number of complaints whose status is `open`.
5. **Audit in order, monotonic `seq`**. A resolve then reopen appends audit actions `resolve`, `reopen` in that order; every audit `seq` is sorted and unique.

**Phase 6. Tickets report (3)**

1. **Exact sums**. `GET /report` returns `open_total_cents` = 500, `archived_total_cents` = 1000, `all_time_total_cents` = 2099.
2. **Archived by `archived_at`**. A row archived but still status-open counts as archived, never open.
3. **Integer cents**. All three `*_total_cents` values are integers.

**Phase 7. Visits report (2)**

1. **Filter, group, sort, limit**. `GET /visits?from=&to=&min_minutes=&limit=` returns the exact per-agent rows (count, total and average minutes), grouped by agent, sorted by total then name, and limited.
2. **Inclusive range, minutes floor**. The `from`/`to` range includes both ends and `min_minutes` is applied as a floor.

**Migrations (6)**. Run with `sqlite-utils migrate`

1. **All recorded in order**. `_sqlite_migrations` for set `agentclinic` lists the four migrations in order: the index, the `resolved_at` backfill, the `open_tickets` view, the `note` column.
2. **Index exists**. `idx_tickets_status_archived` is present.
3. **`resolved_at` backfilled**. Every resolved ticket has `resolved_at` = `2026-01-03T00:00:00`.
4. **`open_tickets` view**. Every row of the view has status `open` and `archived_at IS NULL`.
5. **`note` column**. The `tickets` table has a `note` column.
6. **Re-running is a no-op**. Running `sqlite-utils migrate` again leaves `_sqlite_migrations` unchanged.

Run it with `/challenge hard`. Before: [Medium. The complaints board](medium.md).
