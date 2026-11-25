"""Payload types."""
from typing import TypedDict


class Event(TypedDict, total=True):
    name: str
    at: float


class Labels(TypedDict):
    id: str
