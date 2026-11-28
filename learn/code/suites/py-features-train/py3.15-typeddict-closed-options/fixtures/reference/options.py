"""Option types."""
from typing import TypedDict


class Options(TypedDict, total=False, closed=True):
    retries: int
    verbose: bool


class Env(TypedDict, extra_items=str):
    pass
