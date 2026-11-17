## North Star
Implement the home page for Phase 1.
- [x] app.py holds the FastAPI application as app.
- [x] A shared Jinja2 layout, `templates/base.html`: HTML5 with `lang="en"`, a responsive viewport, Bootstrap 5 from a CDN (CSS in the head, the JS bundle at the end of the body), the favicon `https://www.python.org/static/favicon.ico`, the title "AgentClinic" unless a page sets its own, and a navbar with the "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`).
- [x] The home page at `/` uses that layout: a hero section with the tagline *"Come in. Sit down. Tell us about your human."* and a short welcoming paragraph.
- [x] `uv run --frozen python app.py` starts the app with uvicorn, with reload.
- [x] Tests: `GET /` returns 200 and contains the tagline; `app.py` calls `uvicorn.run` with `reload=True` only under `if __name__ == "__main__".
