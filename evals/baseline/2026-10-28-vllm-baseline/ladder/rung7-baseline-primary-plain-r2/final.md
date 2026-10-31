Successfully implemented the Phase 2 Complaints Board features as specified in `specs/phase-2-board.md`.

Changes made:
1. Created `models.py` with `Complaint` class and seeded `complaints` list (including "Scope creep never ends.").
2. Updated `app.py` to import `complaints` and add `GET /complaints` route.
3. Added `templates/complaints.html` to display the complaints board using Bootstrap cards.
4. Updated `tests/test_app.py` with a test for `GET /complaints` verifying status 200 and presence of the seeded complaint.
5. Ran tests – all pass (`test_home_page` and `test_complaints_board`).

The home page remains functional, and the new `/complaints` endpoint shows the Complaints Board.