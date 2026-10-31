Implemented the resolve and reopen functionality as specified in `specs/phase-4-resolve-reopen.md`. Changes include:

1. Added `status` field to `Complaint` model with default "open".
2. Added `/complaints/{id}/resolve` and `/complaints/{id}/reopen` routes in `app.py`.
3. Updated `complaints.html` to display status badge and appropriate buttons (Resolve/Reopen) based on complaint status.

The board now shows "Open" or "Resolved" badges, and buttons toggle between Resolve and Reopen actions, redirecting to the board with 303 after POST.