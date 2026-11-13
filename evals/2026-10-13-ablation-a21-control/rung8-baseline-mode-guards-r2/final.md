The implementation of specs/phase-3-add.md is complete. The Complaints Board now includes a form for submitting new complaints via `POST /complaints`, which redirects to the board with a 303 status. The tests pass, confirming the functionality works as required.

Changes made:
- Updated `app.py` to handle `POST /complaints` with RedirectResponse and proper imports.
- Modified `templates/complaints.html` to include a complaint submission form.
- Enhanced `tests/test_board.py` with a test for the POST endpoint, which now passes.

The task is done.