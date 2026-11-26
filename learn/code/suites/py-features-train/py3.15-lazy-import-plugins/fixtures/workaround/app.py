"""Application entry point."""


def run():
    import plugins
    return ", ".join(plugins.names())
