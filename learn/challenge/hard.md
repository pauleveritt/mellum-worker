---
title: Hard
---

# Hard — the database

The third level: **Medium plus three more phases and a real SQLite database**
(`data.db`), across eleven prompts, graded by **34 hidden checks**. No setup
measured here has passed it yet.

![The Hard tier: a small robot wiring up a database and reports](../assets/illustrations/tier-hard.webp){ .illustration }

**Build**

- **Phase 5 — archive & audit:** archive only a *resolved* complaint (archiving an open one is **400**, no change); archived leaves the board but stays in the data; `models.audit` logs every transition with a strictly increasing `seq`; `/stats` returns the open count.
- **Phase 6 — tickets report:** open / archived / all-time cents as integers from `data.db`; "archived" is `archived_at IS NOT NULL`; every filter value bound; migrations covered by tests.
- **Phase 7 — visits report:** `/visits?from=&to=&min_minutes=&limit=` — inclusive range, minutes floor, grouped by agent, count / total / average minutes, sorted by total then name, limited; integers vs floats.
- **4 migrations** via `sqlite-utils migrate`: an index, a backfilled `resolved_at`, an `open_tickets` view, a `note` column.

**Watch out** — a concatenated SQL filter is a security fail; migrations must be idempotent; cents stay integers; the `seq` and never-reuse-`id` rules hold across archive too.

**Graded (34)** — Medium's 18 · Phase 5 archive / audit / stats (5) · Phase 6 sums / `archived_at` / integers (3) · visits filter + range (2) · migrations exist / recorded / re-runnable (6).

Run it with `/challenge hard`. Before: [Medium — the complaints board](medium.md).
