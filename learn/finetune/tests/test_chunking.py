"""chunk_bounds: cached-chunk bounds for long sequences, with no chunk too short to train through."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chunking import MIN_CHUNK, chunk_bounds  # noqa: E402


def targets(bounds):
    """Each chunk (s, e) predicts targets s+1..e-1; every target must appear exactly once."""
    return [t for s, e in bounds for t in range(s + 1, e)]


@pytest.mark.parametrize("n", [1, 2, 5, 2047, 2048, 2049, 2050, 4096, 4099, 4106, 6150, 41000])
def test_every_target_once_and_no_short_chunk(n):
    bounds = chunk_bounds(n, 2048)
    assert targets(bounds) == list(range(1, n))
    assert bounds[0][0] == 0 and bounds[-1][1] == n
    if n > MIN_CHUNK:
        assert min(e - s for s, e in bounds) >= MIN_CHUNK


def test_a_tiny_tail_is_folded_into_the_chunk_before():
    # the library's iterator gives (0, 2048), (2047, 4096), (4095, 4099): a 4-token query MLX can't train through
    assert chunk_bounds(4099, 2048) == [(0, 2048), (2047, 4099)]


def test_long_tails_stay_separate():
    assert chunk_bounds(4096 + 500, 2048) == [(0, 2048), (2047, 4096), (4095, 4596)]
