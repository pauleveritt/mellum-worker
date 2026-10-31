from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_report_sums_are_exact():
    data = client.get("/report").json()
    assert data["open_total_cents"] == 500
    assert data["archived_total_cents"] == 1000
    assert data["all_time_total_cents"] == 2099


def test_archived_is_by_archived_at_not_status():
    # Ticket 5 is status='open' but has archived_at set: archived, not open.
    data = client.get("/report").json()
    assert data["open_total_cents"] == 500  # not 800 (would include the archived-but-open row)
    assert data["archived_total_cents"] == 1000
