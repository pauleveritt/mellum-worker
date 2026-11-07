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

Run `uv sync --frozen` before a phase. Use `uv run --frozen` for commands.
