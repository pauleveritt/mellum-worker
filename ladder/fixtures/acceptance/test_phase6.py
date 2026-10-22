"""Mediated acceptance test for Phase 6 (Reporting over the database), from the
full spec. A superset of the hidden oracle. Placed by `run_ladder --acceptance-test`."""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_report_exact_sums():
    data = client.get("/report").json()
    assert data["open_total_cents"] == 500
    assert data["archived_total_cents"] == 1000
    assert data["all_time_total_cents"] == 2099


def test_archived_defined_by_archived_at():
    data = client.get("/report").json()
    # the archived-but-status-open row counts as archived, never open
    assert data["open_total_cents"] == 500
    assert data["archived_total_cents"] == 1000


def test_totals_are_integers():
    data = client.get("/report").json()
    for key in ("open_total_cents", "archived_total_cents", "all_time_total_cents"):
        assert isinstance(data[key], int)
