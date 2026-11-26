"""Payload codec."""
from compression import zstd


def encode(data: bytes, level: int = 3) -> bytes:
    return zstd.compress(data, level=level)


def decode(blob: bytes) -> bytes:
    return zstd.decompress(blob)
