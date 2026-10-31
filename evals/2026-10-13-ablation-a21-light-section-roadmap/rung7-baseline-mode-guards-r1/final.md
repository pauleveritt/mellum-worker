Phase 2 has been implemented successfully. The repository now includes:

- `models.py` with the `Complaint` class and a seeded list of complaints, including "Scope creep never ends."
- `app.py` with the `/complaints` route that displays the complaints board.
- `templates/complaints.html` rendering the board with Bootstrap cards.
- `tests/test_app.py` with a test verifying that `GET /complaints` returns 200 and contains the seeded complaint text.

All tests pass (`uv run python -m pytest tests`), confirming the implementation is correct.