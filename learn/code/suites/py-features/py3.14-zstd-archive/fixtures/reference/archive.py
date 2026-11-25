"""Log archiving."""
from pathlib import Path

from compression import zstd


def pack(path) -> Path:
    path = Path(path)
    out = path.with_name(path.name + ".zst")
    out.write_bytes(zstd.compress(path.read_bytes()))
    return out


def unpack(path) -> Path:
    path = Path(path)
    out = path.with_name(path.name.removesuffix(".zst"))
    out.write_bytes(zstd.decompress(path.read_bytes()))
    return out
