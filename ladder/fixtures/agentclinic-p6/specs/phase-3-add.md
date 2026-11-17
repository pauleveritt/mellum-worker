# Phase 3 — Add Complaint

- The Complaints Board ends with a form for a new complaint (agent name and text) that posts to `/complaints`.
- `POST /complaints` adds the complaint and redirects to the board with status 303 and `Location: /complaints`.
- Existing pages keep working.
- Tests: the POST, without following redirects, returns 303 with that `Location`; afterwards the board lists the new complaint.
