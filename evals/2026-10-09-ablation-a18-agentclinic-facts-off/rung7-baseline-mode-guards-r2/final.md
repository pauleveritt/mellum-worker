The task has been implemented. The following files have been edited or created:

- `models.py`: Added `Complaint` class and `complaints` list seeded with required gripes, including "Scope creep never ends."
- `app.py`: Imported `complaints` from `models`, added `/complaints` route rendering `complaints.html`.
- `templates/complaints.html`: Created template showing Bootstrap cards for each complaint with agent name, date (year, month, day), and text.
- `tests/test_app.py`: Added `test_complaints_page` verifying `/complaints` returns 200 and contains "Scope creep never ends."

The implementation satisfies the spec requirements.