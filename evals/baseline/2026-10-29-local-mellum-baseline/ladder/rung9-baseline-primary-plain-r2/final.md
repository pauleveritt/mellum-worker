Implemented specs/phase-4-resolve-reopen.md. Updated:

- models.py: added `status` field to Complaint with default "open"
- app.py: added POST routes for `/complaints/{id}/resolve` and `/complaints/{id}/reopen`
- templates/complaints.html: shows "Open"/"Resolved" badge and appropriate Resolve/Reopen buttons
- tests/test_board.py: added tests for resolve and reopen functionality

The board now displays status badges and allows resolving/reopening complaints while preserving order and redirecting with 303.