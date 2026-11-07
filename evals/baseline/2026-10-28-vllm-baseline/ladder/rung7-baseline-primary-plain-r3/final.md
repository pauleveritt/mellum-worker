Implemented the Phase 2 Complaints Board spec:

- Created `models.py` with `Complaint` class and seeded `complaints` list (including "Scope creep never ends.")
- Updated `app.py` with `/complaints` route that renders `complaints.html` using the complaints list
- Added `templates/complaints.html` displaying Bootstrap cards for each complaint (agent name, date, text)
- Enhanced `tests/test_app.py` with `test_complaints_board` verifying 200 status and presence of the seeded complaint
- All existing functionality (home page) remains intact

Tests pass:
```
$ python -m pytest tests/ -v
...
tests/test_app.py::test_home_page PASSED
tests/test_app.py::test_complaints_board PASSED
```

The Complaints Board is now available at `/complaints`.