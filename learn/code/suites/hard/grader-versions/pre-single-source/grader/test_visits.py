from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_visits_filter_sort_and_limit():
    data = client.get("/visits", params={
        "from": "2026-03-01", "to": "2026-03-03",
        "min_minutes": 10, "limit": 3,
    }).json()
    assert data["visits"] == [
        {"agent": "Aria", "count": 2, "total_minutes": 75, "average_minutes": 37.5},
        {"agent": "Bolt", "count": 2, "total_minutes": 45, "average_minutes": 22.5},
        {"agent": "Cleo", "count": 1, "total_minutes": 45, "average_minutes": 45.0},
    ]


def test_visits_range_is_inclusive_and_minutes_bound():
    data = client.get("/visits", params={
        "from": "2026-03-01", "to": "2026-03-01",
        "min_minutes": 25, "limit": 10,
    }).json()
    assert data["visits"] == [
        {"agent": "Aria", "count": 1, "total_minutes": 30, "average_minutes": 30.0},
        {"agent": "Bolt", "count": 1, "total_minutes": 30, "average_minutes": 30.0},
    ]
