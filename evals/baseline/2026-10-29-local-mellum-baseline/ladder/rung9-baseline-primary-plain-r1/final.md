Implemented specs/phase-4-resolve-reopen.md by updating:

- `models.py`: Added `id` and `status` fields to `Complaint`, initialized with unique IDs and default status "open".
- `app.py`: Added `POST /complaints/{id}/resolve` and `POST /complaints/{id}/reopen` routes that update status and redirect with 303.
- `templates/complaints.html`: Added status badge ("Open"/"Resolved") and appropriate Resolve/Reopen buttons based on complaint status.
- `tests/test_board.py`: Added tests for resolve and reopen functionality verifying status changes and redirects.

All changes satisfy the phase 4 specs.