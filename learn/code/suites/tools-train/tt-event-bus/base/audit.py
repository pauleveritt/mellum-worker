"""Records saved documents by listening on the bus."""


def attach(bus, log):
    def on_saved(payload):
        log.append(f"saved {payload['id']}")
    bus.subscribe("saved", on_saved)
    return on_saved
