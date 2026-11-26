"""Metric payload types."""
from typing import TypedDict


class Sample(TypedDict, total=True):
    name: str
    value: float


class Counters(TypedDict):
    host: str
