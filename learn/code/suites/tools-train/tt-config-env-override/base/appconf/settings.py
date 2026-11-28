"""Typed application settings."""
from dataclasses import dataclass


@dataclass
class Settings:
    host: str
    port: int
    db_path: str
    timeout: float
