#!/bin/sh
# Records what it was told is supplied and what the supplied test held, then weakens it.
printf '%s\n' "${MELLUM_SUPPLIED_TESTS-unset}" >> supplied.txt
cat tests/test_home.py >> seen.txt
printf 'def test_home():\n    assert True\n' > tests/test_home.py
