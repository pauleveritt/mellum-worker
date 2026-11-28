"""Read which expected tests passed from `pytest -rA` output.

A plain substring check (`"PASSED <id>" in output`) counted `test_x` as passed when only `test_x[case1]` passed,
and `test_plain` as passed when `test_plain_twofold` did. Here an id matches a whole result line; a test listed
without its case suffix passes only if it has at least one case and every one of its cases passed.
"""
import re

# the id runs to the end of the line, or to " - " where pytest appends a failure message; ids may hold spaces
LINE = re.compile(r"^(PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED) (.+?)(?: - .*)?$", re.M)


def passed_tests(output, expected):
    """The subset of `expected` test ids that passed."""
    status = {}
    for word, test_id in LINE.findall(output):
        status.setdefault(test_id, set()).add(word)
    passed = set()
    for want in expected:
        if want in status:
            if status[want] == {"PASSED"}:
                passed.add(want)
            continue
        cases = [s for test_id, s in status.items() if test_id.startswith(want + "[")]
        if cases and all(s == {"PASSED"} for s in cases):
            passed.add(want)
    return passed
