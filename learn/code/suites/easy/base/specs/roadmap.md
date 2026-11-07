# AgentClinic roadmap

Four ordered phases. Each builds on the one before. A request names one
phase; the run ends when that phase's tests pass, and the next phase waits
for its own request.

This file is the authority for every phase: each one ends with an
**Acceptance** list that says when the phase is done; every item on it counts. The mission and the tech stack are in
this folder; the project's notes are in `AGENTS.md`.

## Checking your work

- Check each phase in process with `uv run --frozen python -m pytest tests`,
  using `TestClient` (from `starlette.testclient`) to call the routes.
- Check the work that way, never by starting a server: `uv run --frozen python
  app.py` is how a person runs the app, and it does not return. It must still
  work: a phase can require it, and the checks start it themselves.
- Run Python commands with `uv run --frozen`; use the existing dependencies.

## Layout

- `app.py` — the FastAPI application, at the project root.
- `models.py` — the complaint model, at the project root.
- `templates/` — Jinja2 templates.
- `tests/` — pytest tests.

- Other Python modules or packages — optional local helpers.

## Phase 1 — Home Page

- `app.py` holds the FastAPI application as `app`.
- A shared Jinja2 layout, `templates/base.html`: HTML5 with `lang="en"`, a responsive viewport, Bootstrap 5 from a CDN (CSS in the head, the JS bundle at the end of the body), the favicon `https://www.python.org/static/favicon.ico`, the title "AgentClinic" unless a page sets its own, and a navbar with the "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`).
- The home page at `/` uses that layout: a hero section with the tagline *"Come in. Sit down. Tell us about your human."* and a short welcoming paragraph.
- `uv run --frozen python app.py` starts the app with uvicorn, with reload,
  from an `if __name__ == "__main__"` block (for a person to run, not for checking).

**Acceptance.**

- `GET /` answers 200 and the page contains the tagline, word for word.
- The page starts `<!DOCTYPE html>` and `<html lang="en">`.
- The navbar shows `AgentClinic` and has a link reading `Home` to `/` and one
  reading `Complaints` to `/complaints`.
- The home page is rendered from `templates/home.html`, which extends the shared
  layout `templates/base.html`.
- The layout's head has a responsive viewport, the Bootstrap 5 CSS from a CDN
  and the favicon `https://www.python.org/static/favicon.ico`; the Bootstrap 5
  JS bundle from a CDN is the last thing in its body.
- A page's title is `AgentClinic` by default, and a page that extends the layout
  can set its own title instead.
- The home page has a hero section holding the tagline, and a short welcoming
  paragraph.
- `uv run --frozen python app.py` starts uvicorn from an
  `if __name__ == "__main__"` block in `app.py`, with reload on, and keeps
  serving `GET /` until it is stopped.
- `uv run --frozen python -m pytest tests` passes against the project's own
  test, `tests/test_home.py`, and any tests the phase adds.

## Phase 2 — Complaints Board

- A complaint, `Complaint` in `models.py`, has an agent name, its text, and a UTC creation `timestamp` set automatically for each new complaint.
- `models.py` keeps complaints in a module-level list, `complaints`, seeded with three to five typical AI-agent gripes, one of them exactly `Scope creep never ends.`
- `GET /complaints` shows a "Complaints Board" in the shared layout: one Bootstrap card per complaint with the agent name, the date (year, month and day) and the text.
- The home page keeps working.

**Acceptance.**

- `GET /complaints` answers 200, contains the heading `Complaints Board`, and
  keeps the shared layout: doctype, `lang="en"`, brand and both nav links.
- Each complaint is a `.card` whose text carries the agent's name, the
  complaint text and a date showing year, month and day.
- `models.py` defines `Complaint(agent_name, text)`: both construct
  positionally, and each gets its own timezone-aware `timestamp` by default.
- `models.complaints` is a module-level list of three to five seeded
  complaints, one with the text exactly "Scope creep never ends.".
- Phase 1 still passes.

## Phase 3 — Add Complaint

- The Complaints Board ends with a form for a new complaint (agent name and text) that posts to `/complaints`.
- `POST /complaints` adds the complaint and redirects to the board with status 303 and `Location: /complaints`.
- Existing pages keep working.

**Acceptance.**

- The board ends with a form that posts to `/complaints`, with an
  `agent_name` text input, a `text` textarea and a submit control.
- `POST /complaints` appends the complaint and answers 303 with
  `Location: /complaints`.
- The posted complaint appears on the board at the next `GET /complaints`.
- Phases 1 and 2 still pass.

## Phase 4 — Resolve and Reopen

- Each complaint gets a unique, stable integer `id`, assigned automatically and never reused; `Complaint(agent_name, text)` still works.
- Each complaint has a status, `"open"` unless changed.
- `POST /complaints/{id}/resolve` marks a complaint resolved and `POST /complaints/{id}/reopen` marks it open again; both redirect to the board with 303.
- The board shows a badge reading exactly "Open" or "Resolved", and a Resolve button for an open complaint or a Reopen button for a resolved one.
- Resolving or reopening never changes the order of the board.

**Acceptance.**

- `Complaint` also has `id: int` and `status: str`, and `Complaint(agent_name,
  text)` still constructs positionally: each new complaint's `id` is unique and
  greater than every earlier one, `status` starts as `open`, and how that is
  achieved is the implementer's choice.
- The seeded complaints have distinct ids.
- Each card shows `Open` or `Resolved` and a button that posts to its route.
- `POST /complaints/{id}/resolve` marks that complaint resolved and answers 303
  with `Location: /complaints`; the board then shows `Resolved`.
- `POST /complaints/{id}/reopen` marks it open and answers the same way.
- Resolving or reopening never changes the board's order.
- Phases 1 to 3 still pass.
