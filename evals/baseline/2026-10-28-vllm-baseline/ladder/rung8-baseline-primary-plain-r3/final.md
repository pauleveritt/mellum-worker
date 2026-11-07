Implementation of specs/phase-3-add.md is complete. The following changes were made:

1. **app.py**: Added imports for `Form` and `RedirectResponse`, updated the model import to include `Complaint`, and implemented the `POST /complaints` route to handle new complaints and redirect with status 303.

2. **templates/complaints.html**: Added a form at the end of the complaints board for submitting new complaints with fields for agent name and text, posting to `/complaints`.

3. **tests/test_app.py**: Added a test `test_complaints_post` verifying that POSTing to `/complaints` returns 303 redirect and that the new complaint appears on the board.

The Complaints Board now allows users to submit new complaints via a form, and existing functionality remains intact.