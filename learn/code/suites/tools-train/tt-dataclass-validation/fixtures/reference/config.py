"""Server configuration."""
from dataclasses import MISSING, dataclass, field, fields


class ConfigError(ValueError):
    """A configuration dict is invalid; the message names the offending field."""



def _matches(value, expected):
    """True when value fits the annotation; bool never counts as int."""
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == list[str]:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    return isinstance(value, expected)
@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool = False
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        known = {f.name: f for f in fields(cls)}
        for key in data:
            if key not in known:
                raise ConfigError(f"unknown field {key!r}")
        values = {}
        for name, f in known.items():
            if name not in data:
                if f.default is MISSING and f.default_factory is MISSING:
                    raise ConfigError(f"missing required field {name!r}")
                continue
            value = data[name]
            if not _matches(value, f.type):
                raise ConfigError(f"field {name!r} expects {f.type}, got {type(value).__name__}")
            values[name] = value
        return cls(**values)
