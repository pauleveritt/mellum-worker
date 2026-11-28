"""A tiny in-process event bus."""


class EventBus:
    def subscribe(self, event, handler):
        raise NotImplementedError

    def unsubscribe(self, event, handler):
        raise NotImplementedError

    def publish(self, event, payload=None):
        raise NotImplementedError
