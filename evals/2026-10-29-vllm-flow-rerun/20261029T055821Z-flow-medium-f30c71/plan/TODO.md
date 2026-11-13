## North Star
A mobile-first application that empowers users to report, track, and resolve community complaints through an intuitive four-phase workflow.
- [x] Add a stable `id: int` field to the `Complaint` dataclass in `models.py`, placed after the existing `agent_name`, `text` and `timestamp` fields so `Complaint(agent_name, text)` still constructs positionally; give it an automatic default (for example, an auto-incrementing counter) so it is never required as a constructor argument, is unique, and is never reused or recomputed from its position in the list
- [ ] Add a `status: str` field to `Complaint`, defaulting to `"open"`
- [ ] When adding the new routes to `app.py`, insert them alongside the existing routes — do not remove, replace, or rewrite any route that already works
- [ ] Add `POST /complaints/{complaint_id}/resolve` in `app.py`: set that complaint's `status` to `"resolved"`, then redirect to `GET /complaints` (`RedirectResponse`, status 303)
- [ ] Add `POST /complaints/{complaint_id}/reopen` in `app.py`: set that complaint's `status` back to `"open"`, then redirect the same way
- [ ] In `templates/complaints.html`, show each complaint's status as a badge reading exactly "Open" or "Resolved"
- [ ] For an open complaint, show a "Resolve" button (a form posting to its resolve route); for a resolved complaint, show a "Reopen" button instead
- [ ] Complaints stay in the same order they appear today — resolving or reopening a complaint must not move it
- [ ] Write tests in `tests/test_app.py`: resolving an open complaint changes its status and redirects with 303; reopening a resolved complaint changes it back; the complaint list order is unchanged after either action
