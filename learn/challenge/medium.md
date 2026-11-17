---
title: Medium
---

# Medium. The complaints board

The second level: **Easy plus three more phases** in one session, graded by **18
hidden checks**. The run is now cumulative and stateful. Every new phase must
keep the earlier ones green.

![The Medium tier: a small robot building a complaints board](../assets/illustrations/tier-medium.webp){ .illustration }

**Build**

- **Phase 2. Board:** `Complaint(agent_name, text)` in `models.py` (auto UTC `timestamp`); a seeded `complaints` list of 3–5, one exactly *"Scope creep never ends."*; `GET /complaints` renders a Bootstrap card each.
- **Phase 3. Add:** a form POSTs to `/complaints`, appends, and redirects **303** to the board, where it appears.
- **Phase 4. Resolve/reopen:** a unique, never-reused integer `id` (the constructor still works); an `open`/`resolved` status; resolve & reopen routes that redirect 303; a badge and button per card; the board order never changes.

**Watch out**. Every new phase must keep the earlier ones green, and assigning the `id` in the route instead of on the model fails Phase 4 while all else passes.

## What each check verifies

Eighteen checks: **Easy's four re-run** (the Phase-1 layout must stay green), plus fourteen new ones. A phase passes only with every earlier phase still green.

**Phase 2. Board (6)**

1. **Seed complaint still shown**. `GET /complaints` → `200` and contains *"Scope creep never ends."*
2. **Shared layout preserved**. The board also carries the HTML5 doctype, `lang="en"`, `AgentClinic`, and the Home / Complaints nav links.
3. **Board heading**. The board contains the text *Complaints Board*.
4. **Seed details rendered**. At least one `.card` per seed complaint, each showing that complaint's agent name, its text, and its timestamp's year, month and day.
5. **Model contract**. `Complaint` has `agent_name`, `text` and a `timestamp` with a default factory; two new complaints get distinct, timezone-aware timestamps.
6. **Seed count**. The seed list holds between three and five complaints.

**Phase 3. Add (3)**

1. **POST redirects 303**. `POST /complaints` with `agent_name` and `text` returns `303` with `Location: /complaints` (checked with redirects off).
2. **New complaint appears**. After posting, `GET /complaints` shows the new agent name and text.
3. **Add form present**. The board has a `method="post"` form to `/complaints` with `input[name=agent_name]`, `textarea[name=text]` and a submit control.

**Phase 4. Resolve & reopen (5)**

1. **Stable identity**. `Complaint` gains `id` and `status`; `Complaint(agent_name, text)` still constructs positionally; ids increase and differ; a new complaint starts `open`.
2. **Distinct seed ids**. Every seed complaint has a unique `id`.
3. **Resolve**. `POST /complaints/{id}/resolve` → `303` to `/complaints`, and the card then reads *Resolved*.
4. **Reopen**. After resolving, `POST /complaints/{id}/reopen` → `303` to `/complaints`, and the card reads *Open*.
5. **Order unchanged**. Resolving then reopening a complaint leaves the board's card order the same.

Run it with `/challenge medium`. Before: [Easy. The home page](easy.md).
Next: [Hard. The database](hard.md).
