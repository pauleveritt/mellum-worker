Implementation of phase-4-resolve-reopen.md is complete. The following changes were made:

1. **models.py** - Added `status` field with default `"open"` to the `Complaint` dataclass.
2. **app.py** - Added `POST /complaints/{complaint_id}/resolve` and `POST /complaints/{complaint_id}/reopen` endpoints to update complaint status and redirect to the board with 303.
3. **templates/complaints.html** - Updated to display a badge showing "Open" or "Resolved" and appropriate buttons (Resolve for open, Reopen for resolved).
4. **tests/test_app.py** - Added tests for resolve and reopen functionality verifying status changes, redirects, and button labels.

The board now shows stable complaint IDs implicitly via index, status badges, and correct action buttons. Resolving and reopening updates status without changing order.

The implementation satisfies all requirements in specs/phase-4-resolve-reopen.md.