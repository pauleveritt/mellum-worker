"""pairs_to_text: decode token-id pairs to text, keeping which spans training scored."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pairs_to_text import segments  # noqa: E402


def test_segments_split_on_the_mask_and_keep_every_token():
    decode = lambda ids: "".join(chr(96 + i) for i in ids)  # noqa: E731  1->a, 2->b ...
    got = segments([1, 2, 3, 4, 5, 6], [0, 0, 1, 1, 0, 1], decode)
    assert got == [{"train": False, "text": "ab"}, {"train": True, "text": "cd"},
                   {"train": False, "text": "e"}, {"train": True, "text": "f"}]
    assert segments([], [], decode) == []
