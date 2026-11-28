Implemented the home page phase 1 as described in `specs/phase-1-home.md`:

- Created `app.py` with FastAPI application startup via `uvicorn.run(..., reload=True)`.
- Added `templates/base.html` with shared HTML5 layout, Bootstrap 5 CDN, favicon, and navbar.
- Added `templates/home.html` extending `base.html` with hero section containing the tagline *"Come in. Sit down. Tell us about your human."* and welcoming paragraph.
- Verified smoke test: `GET /` returns 200 and contains the tagline.

Files created/updated:
- `app.py`
- `templates/base.html`
- `templates/home.html`

The implementation meets all requirements specified in `specs/phase-1-home.md`.