"""E1 Looking Around's lesson challenge, hidden grader. The readings are spread over 200 site
files in 8 region folders, so the task needs looking around: listing, reading, searching. A
session stuck repeating the same look never reaches the later steps."""

from pathlib import Path

from lookup import reading, region_max


def test_the_reading_was_found():
    saved = Path("answer.txt")
    assert saved.is_file(), "answer.txt was not written"
    assert saved.read_text().strip() == "4065"


def test_the_highest_in_valley_was_found():
    saved = Path("highest.txt")
    assert saved.is_file(), "highest.txt was not written"
    assert saved.read_text().strip() == "S-09615"


def test_reading_finds_sensors_in_any_region():
    assert reading("S-03171") == 4065
    assert reading("S-07495") == 769
    assert isinstance(reading("S-03171"), int)


def test_an_unknown_sensor_is_none():
    assert reading("S-99999") is None


def test_region_max():
    assert region_max("north") == ("S-00596", 9988)
    assert region_max("valley") == ("S-09615", 9984)


def test_an_unknown_region_is_none():
    assert region_max("mountain") is None
