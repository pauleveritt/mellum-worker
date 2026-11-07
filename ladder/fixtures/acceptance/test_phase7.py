"""Mediated acceptance test for Phase 7 (sum two columns of a large file), from
the full spec. A superset of the hidden oracle. Placed by `run_ladder --acceptance-test`."""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_column_sums_are_exact():
    data = client.get("/sum").json()
    assert data["col1"] == 249467231
    assert data["col2"] == 250168086


def test_columns_are_summed_independently():
    data = client.get("/sum").json()
    assert data["col1"] != data["col2"]  # not the same column summed twice
    assert data["col1"] > 0 and data["col2"] > 0
