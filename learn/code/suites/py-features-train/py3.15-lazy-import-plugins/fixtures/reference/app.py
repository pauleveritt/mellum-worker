"""Application entry point."""
lazy import plugins


def run():
    return ", ".join(plugins.names())
