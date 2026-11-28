"""Server configuration."""
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool = False
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
