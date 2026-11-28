from logstats import summarize

LINES = [
    '1.1.1.1 - - [01/Jan/2026:00:00:01 +0000] "GET /b?x=1 HTTP/1.1" 200 10',
    '1.1.1.2 - - [01/Jan/2026:00:00:02 +0000] "GET /a HTTP/1.1" 404 0',
    '1.1.1.3 - - [01/Jan/2026:00:00:03 +0000] "GET /b?x=2 HTTP/1.1" 200 10',
    '1.1.1.4 - - [01/Jan/2026:00:00:04 +0000] "POST /c HTTP/1.1" 503 0',
    '1.1.1.5 - - [01/Jan/2026:00:00:05 +0000] "GET /a HTTP/1.1" 200 10',
    '1.1.1.6 - - [01/Jan/2026:00:00:06 +0000] "GET /c HTTP/1.1" 200 10',
    '1.1.1.7 - - [01/Jan/2026:00:00:07 +0000] "GET /b HTTP/1.1" 301 0',
]


def write_log(tmp_path, lines=LINES):
    path = tmp_path / "access.log"
    path.write_text("\n".join(lines) + "\n")
    return path


def test_counts_status_codes_as_ints(tmp_path):
    summary = summarize(write_log(tmp_path))
    assert summary["status"] == {200: 4, 404: 1, 503: 1, 301: 1}


def test_query_string_is_not_part_of_the_path(tmp_path):
    summary = summarize(write_log(tmp_path), top=1)
    assert summary["top_paths"] == [("/b", 3)]


def test_ties_break_alphabetically_and_top_limits(tmp_path):
    summary = summarize(write_log(tmp_path), top=3)
    assert summary["top_paths"] == [("/b", 3), ("/a", 2), ("/c", 2)]
    assert len(summarize(write_log(tmp_path), top=2)["top_paths"]) == 2
