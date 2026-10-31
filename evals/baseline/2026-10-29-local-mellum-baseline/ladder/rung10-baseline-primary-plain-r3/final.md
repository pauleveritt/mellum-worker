The implementation of phase-5-archive.md has been completed. I've updated:

- `models.py`: Added `audit: list[dict] = []` for tracking status changes
- `app.py`: 
  - Imported `audit` from models
  - Enhanced `set_status` to record audit entries with action and sequence
  - Modified `resolve` and `reopen` routes to pass action names
  - Added `archive` route with validation (only allowed when status is "resolved")
  - Updated `/complaints` board to filter out archived complaints
  - Added `/stats` route to return open complaint count

All requirements from the spec have been implemented without removing existing functionality or adding dependencies.

You can now run the application test suite or start the server to verify the new features.