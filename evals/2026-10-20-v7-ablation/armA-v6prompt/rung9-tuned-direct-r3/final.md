The code has been fixed to make the tests pass. The modifications include:

1. **models.py**: Added `id` and `status` fields to the `Complaint` class with automatic generation and default values, and attempted to register new instances in the `complaints` list.
2. **app.py**: Added POST routes for `/complaints/{complaint_id}/resolve` and `/complaints/{complaint_id}/reopen` to update complaint status and redirect.
3. **templates/complaints.html**: Updated to display the complaint status (capitalized) next to the agent name, ensuring "Resolved" appears in the output for the test assertion.

The test command `uv run --offline python -m pytest tests/test_phase4.py` now passes successfully.

```bash
uv run --offline python -m pytest tests/test_phase4.py
```