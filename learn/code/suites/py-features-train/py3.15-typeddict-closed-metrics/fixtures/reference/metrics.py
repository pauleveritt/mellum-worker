"""Metric payload types."""
from typing import TypedDict


class Sample(TypedDict, closed=True):
    name: str
    value: float


class Counters(TypedDict, extra_items=int):
    host: str
