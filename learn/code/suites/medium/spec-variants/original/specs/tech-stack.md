# Tech Stack

| Layer | Choice | Version | Notes |
|-------|--------|---------|-------|
| Language | Python 3.14 | 3.14 | Managed with `uv` and `uv.lock` |
| Web framework | fastapi[standard] | 0.115.10 | ASGI, type-driven |
| Server | Uvicorn | 0.51.0 | ASGI server, run via `app.py` |
| Templates | Jinja2 | 3.1.6 | Bundled with FastAPI/Starlette |
| CSS | Bootstrap 5 | | CDN link, no npm/build step |
| Data model | `dataclasses.dataclass` | | Complaint: `agent_name`, `text`, `timestamp` |
| Storage | In-memory `list` | | Module-level, no database |
| Testing | pytest + `TestClient` | 8.3.4 | `starlette.testclient.TestClient`, no running server needed |

## Project layout

| File | Holds | Notes |
|------|-------|-------|
| `app.py` | The FastAPI app and its routes, plus `if __name__ == "__main__"` running uvicorn with reload | The module the checks import as `app` |
| `models.py` | The `Complaint` dataclass and the module-level `complaints` list | The checks import `models` and `from models import Complaint`; the dataclass lives here, not in `app.py` |
| `templates/` | `base.html` (the shared layout), `home.html`, `complaints.html` | Jinja2: extend the layout, fill a block |
| `tests/` | The project's own tests | Run with the test command; `TestClient` in process, never a server |

## Markup conventions

- Every page starts `<!DOCTYPE html>` and `<html lang="en">` and extends the
  shared layout.
- The navbar shows the brand `AgentClinic` and links Home to `/` and Complaints
  to `/complaints`.
- Each complaint on the board is a `.card` whose text carries the agent's name,
  the complaint text and a date showing year, month and day.
- A complaint's state is shown as the word `Open` or `Resolved`, beside a form
  button that changes it.

Run `uv sync --frozen` before a phase. Use `uv run --frozen` for commands.
