# Phase 1 — Home Page

- As an agent arriving at the clinic, I want the tagline "Come in. Sit down.
  Tell us about your human." and a short welcome, so I know where I am.
- As a visitor, I want a shared layout with a navbar to Home and Complaints,
  so I can move around.
- As the operator, I want `uv run --frozen python app.py` to start the app with reload.
- As the operator, I want the home page exercised in process with `TestClient`,
  so a change can be checked without a running server.

**Acceptance.**

- `GET /` answers 200 and the page contains the tagline, word for word.
- The page starts `<!DOCTYPE html>` and `<html lang="en">`.
- The navbar shows `AgentClinic` and links Home to `/` and Complaints to
  `/complaints`.
- `uv run --frozen python -m pytest tests` passes against the project's own
  test.
