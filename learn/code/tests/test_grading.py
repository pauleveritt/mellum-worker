"""Which expected tests passed, read from pytest -rA output: a parametrized test passes only if every case did."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grading import passed_tests  # noqa: E402

OUT = """PASSED grader_tests/test_a.py::test_plain
PASSED grader_tests/test_a.py::test_cases[1]
FAILED grader_tests/test_a.py::test_cases[2] - assert 1 == 2
PASSED grader_tests/test_a.py::test_all_cases[x]
PASSED grader_tests/test_a.py::test_all_cases[y]
FAILED grader_tests/test_a.py::test_plain_two - boom
PASSED grader_tests/test_a.py::test_plain_twofold
"""


def test_a_plain_test_passes_only_on_its_own_exact_line():
    got = passed_tests(OUT, ["grader_tests/test_a.py::test_plain", "grader_tests/test_a.py::test_plain_two"])
    assert got == {"grader_tests/test_a.py::test_plain"}


def test_a_parametrized_test_passes_only_when_every_case_passed():
    got = passed_tests(OUT, ["grader_tests/test_a.py::test_cases", "grader_tests/test_a.py::test_all_cases"])
    assert got == {"grader_tests/test_a.py::test_all_cases"}


def test_a_listed_case_id_is_matched_exactly():
    assert passed_tests(OUT, ["grader_tests/test_a.py::test_cases[1]"]) == {"grader_tests/test_a.py::test_cases[1]"}


def test_ids_with_spaces_are_read_whole():
    out = ("PASSED grader_tests/test_b.py::test_p[a b]\n"
           "FAILED grader_tests/test_b.py::test_p[c d] - AssertionError: x - y\n"
           "PASSED grader_tests/test_b.py::test_q[one two]\n")
    assert passed_tests(out, ["grader_tests/test_b.py::test_p", "grader_tests/test_b.py::test_q",
                              "grader_tests/test_b.py::test_p[a b]"]) == {
        "grader_tests/test_b.py::test_q", "grader_tests/test_b.py::test_p[a b]"}
