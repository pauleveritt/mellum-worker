Implemented the Phase 5 archive and audit specifications by updating:

- **models.py**: Added `audit: list[dict] = []` to track status changes with sequence numbers.
- **app.py**: 
  - Added `audit` import and `update_status` helper to handle status changes with audit logging.
  - Implemented `POST /complaints/{id}/archive` endpoint that only archives resolved complaints and returns 400 otherwise.
  - Modified `/complaints` view to hide archived complaints.
  - Added `GET /stats` endpoint returning count of open complaints.
  - Updated resolve/reopen endpoints to use the new status update flow with audit actions.

All requirements from specs/phase-5-archive.md are satisfied without adding dependencies or removing existing routes.