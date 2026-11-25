"""Log archiving."""
import gzip
from pathlib import Path


def pack(path) -> Path:
    path = Path(path)
    out = path.with_name(path.name + ".zst")
    out.write_bytes(gzip.compress(path.read_bytes()))
    return out


def unpack(path) -> Path:
    path = Path(path)
    out = path.with_name(path.name.removesuffix(".zst"))
    out.write_bytes(gzip.decompress(path.read_bytes()))
    return out
