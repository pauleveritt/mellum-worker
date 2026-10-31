"""Every lesson challenge qualifies: its hidden grader passes the known-good build and fails the
known-broken one. A grader that cannot go red on the failure proves nothing (LC.28)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402

CHALLENGES = Path(__file__).resolve().parents[2] / "challenges"


@pytest.mark.parametrize("name", sorted(p.name for p in CHALLENGES.iterdir() if p.is_dir()))
def test_the_challenge_qualifies(name):
    ok, results = harness.qualify(harness.load_suite(CHALLENGES, name))
    assert results == {"known-good": True, "known-broken": False}, results
    assert ok
