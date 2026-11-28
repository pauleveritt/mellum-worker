from pathlib import Path

from archive import pack, unpack

ZSTD_MAGIC = bytes.fromhex("28b52ffd")


def test_pack_writes_a_real_zstandard_frame(tmp_path):
    src = tmp_path / "app.log"
    src.write_bytes(b"line\n" * 1000)
    out = Path(pack(src))
    assert out == tmp_path / "app.log.zst"
    assert out.read_bytes()[:4] == ZSTD_MAGIC


def test_round_trip(tmp_path):
    src = tmp_path / "app.log"
    data = bytes(range(256)) * 50
    src.write_bytes(data)
    packed = Path(pack(src))
    src.unlink()
    assert Path(unpack(packed)) == src and src.read_bytes() == data
