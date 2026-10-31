The task has been completed. The tests pass, and all requirements from specs/phase-4-resolve-reopen.md have been implemented:

- Each complaint now has a unique stable integer `id` and a `status` field (default "open").
- `POST /complaints/{id}/resolve` and `POST /complaints/{id}/reopen` endpoints exist, redirect to the board with 303.
- The board (`complaints.html`) shows a badge "Open" or "Resolved" and appropriate buttons (Resolve for open, Reopen for resolved).
- Order of complaints is unchanged when resolving or reopening.

Test command: `uv run python -m pytest tests` exits 0.

Done.