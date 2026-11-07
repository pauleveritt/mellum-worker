"""Report sums follow private database variations, with real SQL aggregation."""
from grader_tests._contract import client
from grader_tests._database import TICKETS, sql_calls, table_rows

KEYS = ("open_total_cents", "archived_total_cents", "all_time_total_cents")


def _expected(rows):
    return dict(zip(KEYS, (
        sum(cents for _, status, archived, cents in rows if status == "open" and archived is None),
        sum(cents for _, _, archived, cents in rows if archived is not None),
        sum(cents for _, _, _, cents in rows),
    )))


def _report():
    response = client.get("/report")
    assert response.status_code == 200
    return response.json()


def test_report_exact_sums():
    for rows in (TICKETS, [(i, s, a, cents * 3 + i) for i, s, a, cents in TICKETS], []):
        with table_rows("tickets", ("id", "status", "archived_at", "cents"), rows):
            with sql_calls() as (calls, functions):
                data = _report()
            assert data == _expected(rows)
            assert "database-aggregate" in functions, "Ticket sums must be computed in SQLite"
            assert calls, "The report must query the real database"


def test_archived_defined_by_archived_at():
    rows = [(1, "open", "2031-01-01", 13), (2, "resolved", "2031-01-02", 29),
            (3, "open", None, 43), (4, "resolved", None, 67), (5, "open", "", 71)]
    with table_rows("tickets", ("id", "status", "archived_at", "cents"), rows):
        assert _report() == _expected(rows)


def test_totals_are_integers():
    for rows in (TICKETS, []):
        with table_rows("tickets", ("id", "status", "archived_at", "cents"), rows):
            data = _report()
            assert all(type(data[key]) is int for key in KEYS)
