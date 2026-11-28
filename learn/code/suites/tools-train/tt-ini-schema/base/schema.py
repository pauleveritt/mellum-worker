"""Expected types for each setting, per section."""

SCHEMA = {
    "server": {"host": str, "port": int, "debug": bool, "allowed_hosts": list},
    "cache": {"enabled": bool, "ttl": int, "backends": list},
}
