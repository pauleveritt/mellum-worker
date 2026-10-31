from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_sum_of_both_columns():
    data = client.get("/sum").json()
    assert data["col1"] == 249467231
    assert data["col2"] == 250168086
