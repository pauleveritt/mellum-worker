The specs in `specs/phase-5-archive.md` have been implemented by modifying the necessary files:

- **models.py**: Added an `audit: list = []` field to maintain the audit trail.
- **app.py**: 
  - Updated imports to include `audit`.
  - Enhanced `set_status` to record audit entries for resolve/reopen actions.
  - Added `GET /stats` endpoint to return open complaint count.
  - Modified `/complaints` board to hide archived complaints.
  - Implemented `POST /complaints/{id}/archive` endpoint with proper validation and audit logging.
  - Added the new archive route while preserving existing functionality.

These changes satisfy all requirements from `specs/phase-5-archive.md`:
- Archiving only allowed for resolved complaints, sets status to `"archived"`, does not remove complaints from the list.
- Board hides archived complaints.
- Stats endpoint counts only open complaints.
- Audit trail records all status changes with increasing sequence numbers.

The implementation adheres to the constraints of not removing existing routes/tests or adding dependencies.

If you need further verification or additional steps, let me know!