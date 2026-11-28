"""Environment-variable overrides for the loaded settings."""

# variable name -> (Settings attribute, converter)
OVERRIDES = {
    "APP_HOST": ("host", str),
    "APP_PORT": ("port", int),
    "APP_DB_PATH": ("db_path", str),
}


def apply_overrides(settings, env):
    for name, (attr, convert) in OVERRIDES.items():
        if name in env:
            setattr(settings, attr, convert(env[name]))
    return settings
