Implemented the phase 3 add complaint feature as specified in `specs/phase-3-add.md`:

1. Added a complaint form to `templates/complaints.html` that posts to `/complaints`
2. Added POST `/complaints` handler in `app.py` that:
   - Parses form data for agent name and text
   - Creates a new Complaint and adds it to the complaints list
   - Redirects to `/complaints` with status 303
3. Added tests in `tests/test_board.py` verifying:
   - Redirect behavior after POST
   - New complaint appears on board after submission

All changes are complete. The complaint feature now works with existing pages unaffected.