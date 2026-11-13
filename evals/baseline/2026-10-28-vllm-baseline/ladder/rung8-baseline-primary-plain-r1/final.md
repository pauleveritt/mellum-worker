Implemented the Phase 3 add complaint feature as per specs/phase-3-add.md:

1. Updated `app.py` with:
   - Added imports for `Form` and `RedirectResponse`
   - Added `Complaint` import from models
   - Added POST `/complaints` endpoint that:
     - Accepts form data for agent_name and text
     - Appends new complaint to the list
     - Redirects to `/complaints` with 303 status

2. Updated `templates/complaints.html` to include a complaint form:
   - Added form with fields for agent_name and text
   - Form submits to `/complaints` via POST

3. Updated `tests/test_board.py` with a test case for:
   - POSTing a new complaint
   - Verifying 303 redirect with correct Location header
   - Checking that the complaint appears on the board

The Complaints Board now ends with a form for new complaints, and existing functionality remains intact.