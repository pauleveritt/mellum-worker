"""Option types."""
from typing import TypedDict


class Options(TypedDict, total=False):
    retries: int
    verbose: bool


class Env(TypedDict, total=False):
    pass
