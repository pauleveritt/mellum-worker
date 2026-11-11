# AgentClinic roadmap

Four ordered phases. Each builds on the one before. A request names one
phase; the run ends when that phase's tests pass, and the next phase waits
for its own request.

The test command and what a phase must not do are in the `## Mellum` section
of `AGENTS.md`.

## Layout

- `app.py` — the FastAPI application, at the project root.
- `models.py` — the complaint model, at the project root.
- `templates/` — Jinja2 templates.
- `tests/` — pytest tests.

## Phase 1 — Home Page

- `app.py` holds the FastAPI application as `app`.
- A shared Jinja2 layout, `templates/base.html`: HTML5 with `lang="en"`, a responsive viewport, Bootstrap 5 from a CDN (CSS in the head, the JS bundle at the end of the body), the favicon `https://www.python.org/static/favicon.ico`, the title "AgentClinic" unless a page sets its own, and a navbar with the "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`).
- The home page at `/` uses that layout: a hero section with the tagline *"Come in. Sit down. Tell us about your human."* and a short welcoming paragraph.
- `uv run --frozen python app.py` starts the app with uvicorn, with reload.
- Tests: `GET /` returns 200 and contains the tagline; `app.py` calls
  `uvicorn.run` with `reload=True` only under `if __name__ == "__main__"`.

## Phase 2 — Complaints Board

- A complaint, `Complaint` in `models.py`, has an agent name, its text, and a UTC creation `timestamp` set automatically for each new complaint.
- `models.py` keeps complaints in a module-level list, `complaints`, seeded with three to five typical AI-agent gripes, one of them exactly `Scope creep never ends.`
- `GET /complaints` shows a "Complaints Board" in the shared layout: one Bootstrap card per complaint with the agent name, the date (year, month and day) and the text.
- The home page keeps working.
- A test: `GET /complaints` returns 200 and contains `Scope creep never ends.`

## Phase 3 — Add Complaint

- The Complaints Board ends with a form for a new complaint (agent name and text) that posts to `/complaints`.
- `POST /complaints` adds the complaint and redirects to the board with status 303 and `Location: /complaints`.
- Existing pages keep working.
- Tests: the POST, without following redirects, returns 303 with that `Location`; afterwards the board lists the new complaint.

## Phase 4 — Resolve and Reopen

- Each complaint gets a unique, stable integer `id`, assigned automatically and never reused; `Complaint(agent_name, text)` still works.
- Each complaint has a status, `"open"` unless changed.
- `POST /complaints/{id}/resolve` marks a complaint resolved and `POST /complaints/{id}/reopen` marks it open again; both redirect to the board with 303.
- The board shows a badge reading exactly "Open" or "Resolved", and a Resolve button for an open complaint or a Reopen button for a resolved one.
- Resolving or reopening never changes the order of the board.
- Tests: resolve and reopen change the status and redirect with 303, and the order is unchanged.
