from datetime import date

import dates
import report
import textutils


def test_date_helpers_live_in_dates():
    for name in ("parse_date", "format_date", "days_between"):
        assert getattr(dates, name).__module__ == "dates"
    assert dates.format_date(date(2024, 3, 5)) == "5 Mar 2024"
    assert dates.days_between("2024-02-28", "2024-03-01") == 2


def test_old_import_path_still_works():
    from textutils import days_between, format_date, parse_date
    assert parse_date is dates.parse_date
    assert format_date is dates.format_date
    assert days_between is dates.days_between


def test_text_helpers_stay_and_report_unchanged():
    assert textutils.title_case("the art of war") == "The Art of War"
    assert textutils.word_count("a b  c") == 3
    assert report.summary("the plan", "2024-01-30", "2024-02-02") == "The Plan: 30 Jan 2024 to 2 Feb 2024 (3 days)"
