Implementation of `specs/phase-5-archive.md` is complete.

Changes made:
- `models.py`: Added `audit: list[dict] = []` to hold audit trail.
- `app.py`: 
  -Imported `audit` from models.
  -Updated `set_status` to support action-based auditing.
  -Modified `resolve` and `reopen` to record "resolve" and "reopen" actions.
  -Added `POST /complaints/{id}/archive` endpoint with validation and audit entry.
  -Updated `GET /complaints` to hide archived complaints.
  -Added `GET /stats` endpoint returning open complaint count.
  -Adjusted route order and imports accordingly.

All requirements from the spec are satisfied. The application now supports archiving, audit logging, hiding archived complaints, and stats while preserving existing functionality.