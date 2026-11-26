"""Application entry point."""
import plugins


def run():
    return ", ".join(plugins.names())
