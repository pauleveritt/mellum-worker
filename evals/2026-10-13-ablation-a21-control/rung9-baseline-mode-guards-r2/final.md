The task is complete. The following files were edited:

1. **models.py**: Added `id` and `status` fields to `Complaint`, and fixed global variable declaration order.
2. **app.py**: Added routes for `/complaints/{id}/resolve` and `/complaints/{id}/reopen` to handle status changes.
3. **templates/complaints.html**: Added status badge and Resolve/Reopen buttons based on complaint status.

Tests passed:
```
....                                                                     [100%]
=============================== warnings summary ===============================
...
4 passed, 6 warnings in 0.57s
```