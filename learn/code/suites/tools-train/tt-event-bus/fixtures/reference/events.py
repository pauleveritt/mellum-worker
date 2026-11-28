"""A tiny in-process event bus."""
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event, handler):
        self._handlers[event].append(handler)

    def unsubscribe(self, event, handler):
        handlers = self._handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event, payload=None):
        snapshot = list(self._handlers.get(event, []))
        for handler in snapshot:
            handler(payload)
        return len(snapshot)
