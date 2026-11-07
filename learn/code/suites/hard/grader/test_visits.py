"""Visits use private rows, inclusive filters, usable defaults and strict JSON types."""
from datetime import date as Date

from grader_tests._contract import client
from grader_tests._database import VISITS, sql_calls, table_rows


def _expected(rows, start, end, minimum=0, limit=10):
    groups = {}
    for _, agent, date, minutes, _ in rows:
        if start <= date <= end and minutes >= minimum:
            groups.setdefault(agent, []).append(minutes)
    result = [{"agent": agent, "count": len(values), "total_minutes": sum(values),
               "average_minutes": sum(values) / len(values)} for agent, values in groups.items()]
    return sorted(result, key=lambda row: (-row["total_minutes"], row["agent"]))[:limit]


def _check(rows, params):
    response = client.get("/visits", params=params)
    assert response.status_code == 200
    actual = response.json()["visits"]
    assert actual == _expected(rows, params["from"], params["to"],
                               params.get("min_minutes", 0), params.get("limit", 10))
    for row in actual:
        assert type(row["agent"]) is str
        assert type(row["count"]) is int and type(row["total_minutes"]) is int
        assert type(row["average_minutes"]) is float


def test_visits_filter_sort_and_limit():
    for rows in (VISITS, [(i, a, d, m * 2 + i, t) for i, a, d, m, t in VISITS]):
        with table_rows("visits", ("id", "agent", "date", "minutes", "ticket_id"), rows):
            for options in ({}, {"min_minutes": 10}, {"limit": 2},
                            {"min_minutes": 10, "limit": 3}, {"limit": 0}, {"limit": 30}):
                _check(rows, {"from": "2031-04-10", "to": "2031-04-12", **options})


def test_visits_range_is_inclusive_and_minutes_bound():
    with table_rows("visits", ("id", "agent", "date", "minutes", "ticket_id"), VISITS):
        for start, end, minimum in (("2031-04-10", "2031-04-10", 20),
                                    ("2031-04-12", "2031-04-12", 21),
                                    ("2031-04-10", "2031-04-12", 41),
                                    ("2031-04-10", "2031-04-12", 1000),
                                    ("2032-01-01", "2032-01-02", 0)):
            with sql_calls() as (calls, _):
                _check(VISITS, {"from": start, "to": end, "min_minutes": minimum, "limit": 20})
            bound = [value.isoformat() if isinstance(value, Date) else value
                     for _, values in calls for value in values]
            assert start in bound and end in bound and minimum in bound, "Bind request-derived SQL filter values"
