"""Phase 1's own smoke test, in process.

The project's notes say to run `uv run --frozen python -m pytest tests`, and
before this file existed that command had nothing to run. It exercises the app
through `TestClient`, so a change can be checked without starting a server.
The hidden graders are separate and are never copied in while the worker runs.
"""

from starlette.testclient import TestClient

from app import app


def test_home_returns_the_tagline():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text


def test_home_has_the_shared_navigation():
    body = TestClient(app).get("/").text
    assert "AgentClinic" in body
