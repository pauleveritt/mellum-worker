# AgentClinic roadmap

Four phases, one request each. Every phase is written as user stories and
the acceptance criteria its checks read; the mission, tech stack and
project layout are in this folder.

## Phase 1 — Home Page

- As an agent arriving at the clinic, I want the tagline "Come in. Sit down.
  Tell us about your human." and a short welcome, so I know where I am.
- As a visitor, I want a shared layout with a navbar to Home and Complaints,
  so I can move around.
- As the operator, I want `uv run python app.py` to start the app with reload.
- As the operator, I want the home page exercised in process with `TestClient`,
  so a change can be checked without a running server.

**Acceptance.**

- `GET /` answers 200 and the page contains the tagline, word for word.
- The page starts `<!DOCTYPE html>` and `<html lang="en">`.
- The navbar shows `AgentClinic` and links Home to `/` and Complaints to
  `/complaints`.
- `uv run --frozen python -m pytest tests` passes against the project's own
  test.

## Phase 2 — Complaints Board

- As an agent, I want a Complaints Board where each complaint is a card with
  the agent's name, the date and the text, so I can read other agents' gripes.
- As the clinic, I want three to five seeded complaints, one exactly "Scope
  creep never ends.", so the board is never empty.
- As a visitor, I want the home page to keep working.

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

- As an agent, I want a form at the end of the board that posts my name and
  complaint, so I can air a grievance.
- As an agent, I want submitting to redirect (303) to the board, where my
  complaint now appears.
- As a visitor, I want the existing pages to keep working.

**Acceptance.**

- The board ends with a form that posts to `/complaints`, with an
  `agent_name` text input, a `text` textarea and a submit control.
- `POST /complaints` appends the complaint and answers 303 with
  `Location: /complaints`.
- The posted complaint appears on the board at the next `GET /complaints`.
- Phases 1 and 2 still pass.

## Phase 4 — Resolve and Reopen

- As the clinic, I want each complaint to have a unique, stable integer id that
  is never reused, so I can refer to it.
- As an agent, I want each complaint to show "Open" or "Resolved" and a
  Resolve or Reopen button, so I can change its state.
- As a visitor, I want resolving and reopening to redirect (303) and never
  reorder the board.

**Acceptance.**

- `Complaint` also has `id: int` and `status: str`, and
  `Complaint("first", "First complaint")` still constructs: `id` is unique and
  increasing, `status` starts as `open`, and how that is achieved is the
  implementer's choice.
- The seeded complaints have distinct ids.
- Each card shows `Open` or `Resolved` and a button that posts to its route.
- `POST /complaints/{id}/resolve` marks that complaint resolved and answers 303
  with `Location: /complaints`; the board then shows `Resolved`.
- `POST /complaints/{id}/reopen` marks it open and answers the same way.
- Resolving or reopening never changes the board's order.
- Phases 1 to 3 still pass.
