from db import sql


def test_values_become_placeholders():
    name, age = "ada", 36
    assert sql(t"SELECT * FROM users WHERE name = {name} AND age > {age}") == (
        "SELECT * FROM users WHERE name = ? AND age > ?", ["ada", 36])


def test_injection_text_stays_a_value():
    evil = "x'; DROP TABLE users; --"
    query, params = sql(t"SELECT 1 WHERE a = {evil}")
    assert query == "SELECT 1 WHERE a = ?" and params == [evil]


def test_no_interpolations():
    assert sql(t"SELECT 1") == ("SELECT 1", [])
