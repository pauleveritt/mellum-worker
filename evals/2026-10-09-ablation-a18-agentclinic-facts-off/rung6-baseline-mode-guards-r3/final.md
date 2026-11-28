successfully completed the implementation of specs/phase-1-home.md. The FastAPI application now includes:

- `app.py` with the FastAPI instance and a route to run via `uvicorn` with reload
- `templates/base.html` with Bootstrap 5, navbar, and favicon
- `templates/home.html` with the hero section and tagline
- Updated `pyproject.toml` with `uvicorn` dependency
- A test file `tests/test_home.py` that verifies the home page contains the tagline

The test command `uv run --offline -m pytest -q` exits 0, confirming completion.