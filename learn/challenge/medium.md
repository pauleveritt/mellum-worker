---
title: Medium
---

# Medium — the complaints board

The second level: **Easy plus three more phases** in one session, graded by **18
hidden checks**. The run is now cumulative and stateful — every new phase must
keep the earlier ones green.

**Build**

- **Phase 2 — board:** `Complaint(agent_name, text)` in `models.py` (auto UTC `timestamp`); a seeded `complaints` list of 3–5, one exactly *"Scope creep never ends."*; `GET /complaints` renders a Bootstrap card each.
- **Phase 3 — add:** a form POSTs to `/complaints`, appends, and redirects **303** to the board, where it appears.
- **Phase 4 — resolve/reopen:** a unique, never-reused integer `id` (the constructor still works); an `open`/`resolved` status; resolve & reopen routes that redirect 303; a badge and button per card; the board order never changes.

**Watch out** — every new phase must keep the earlier ones green, and assigning the `id` in the route instead of on the model fails Phase 4 while all else passes.

**Graded (18)** — Easy's 4 · board heading / seed / details / layout / model / seed-count (6) · add form / 303 / appears (3) · id / status / order (5).

Run it with `/challenge medium`. Before: [Easy — the home page](easy.md).
Next: [Hard — the database](hard.md).
