"""Payload types."""
from typing import TypedDict


class Event(TypedDict, closed=True):
    name: str
    at: float


class Labels(TypedDict, extra_items=str):
    id: str
