# Phase 2 — Complaints Board

- A complaint, `Complaint` in `models.py`, has an agent name, its text, and a UTC creation timestamp set automatically for each new complaint.
- `models.py` keeps complaints in a module-level list, `complaints`, seeded with three to five typical AI-agent gripes, one of them exactly `Scope creep never ends.`
- `GET /complaints` shows a "Complaints Board" in the shared layout: one Bootstrap card per complaint with the agent name, the date (year, month and day) and the text.
- The home page keeps working.
- A test: `GET /complaints` returns 200 and contains `Scope creep never ends.`
