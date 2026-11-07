Files changed:

1. **models.py** - Added `id` and `status` fields to `Complaint` with auto-incrementing stable integer IDs and default "open" status. Implemented `__post_init__` to assign IDs.
2. **app.py** - Added two new POST routes: `/complaints/{complaint_id}/resolve` and `/complaints/{complaint_id}/reopen` to handle status changes with redirects.
3. **templates/complaints.html** - Added a badge showing the complaint status ("Open" or "Resolved") next to the agent name.

Test output:
```
$ uv run python -m pytest tests/test_phase4.py
tests/test_phase4.py ..                                                  [100%]

=============================== warnings summary ===============================
...
======================== 2 passed, 6 warnings in 0.14s =========================
```

Or with verbose:
```
$ uv run python -m pytest tests/test_phase4.py -v
tests/test_phase4.py::test_new_complaints_get_distinct_stable_integer_ids_and_default_open PASSED [ 50%]
tests/test_phase4.py::test_resolve_and_reopen_redirect_303_change_status_and_keep_order PASSED [100%]

=============================== warnings summary ===============================
...
======================== 2 passed, 6 warnings in 0.16s =========================
```