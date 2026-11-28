"""Payload codec."""
import zlib


def encode(data: bytes, level: int = 3) -> bytes:
    return zlib.compress(data, min(level, 9))


def decode(blob: bytes) -> bytes:
    return zlib.decompress(blob)
