"""A tiny in-process event bus."""


class EventBus:
    def __init__(self):
        self._handlers = {}

    def subscribe(self, event, handler):
        self._handlers.setdefault(event, []).append(handler)

    def unsubscribe(self, event, handler):
        handlers = self._handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event, payload=None):
        count = 0
        for handler in self._handlers.get(event, []):  # live list: removal mid-loop skips the next one
            handler(payload)
            count += 1
        return count
