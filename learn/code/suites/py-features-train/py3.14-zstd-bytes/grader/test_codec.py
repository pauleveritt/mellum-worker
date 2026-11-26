from codec import decode, encode

ZSTD_MAGIC = bytes.fromhex("28b52ffd")


def test_encode_makes_a_real_zstandard_frame():
    assert encode(b"abc" * 500)[:4] == ZSTD_MAGIC


def test_round_trip_at_any_level():
    data = bytes(range(256)) * 40
    for level in (1, 3, 19):
        assert decode(encode(data, level)) == data


def test_higher_level_is_not_larger_on_repetitive_data():
    data = b"metrics,host=a value=1\n" * 2000
    assert len(encode(data, 19)) <= len(encode(data, 1))
