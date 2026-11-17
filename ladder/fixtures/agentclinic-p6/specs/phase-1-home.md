# Phase 1 — Home Page

- `app.py` holds the FastAPI application as `app`.
- A shared Jinja2 layout, `templates/base.html`: HTML5 with `lang="en"`, a responsive viewport, Bootstrap 5 from a CDN (CSS in the head, the JS bundle at the end of the body), the favicon `https://www.python.org/static/favicon.ico`, the title "AgentClinic" unless a page sets its own, and a navbar with the "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`).
- The home page at `/` uses that layout: a hero section with the tagline *"Come in. Sit down. Tell us about your human."* and a short welcoming paragraph.
- `python app.py` starts the app with uvicorn, with reload.
- A smoke test: `GET /` returns 200 and contains the tagline.
